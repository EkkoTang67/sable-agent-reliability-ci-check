"""Tests for exact-byte + EIP-712 + request + Base-settlement evidence bundles."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from eth_account import Account
from eth_account.messages import encode_typed_data
from api.evidence_bundle_audit import (
    V03_TYPES,
    _typed_receipt,
    _verify_request_binding,
    _verify_seller_signature,
    _verify_settlement,
    audit_bundle,
)

TX = "0x" + "77" * 32
TOKEN = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
URL = "https://api.example.test/v1/result?kind=demo"
PARAMS = "{}"
BODY = b'{"status":"complete","value":42}'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def make_signed_receipt():
    seller = Account.create()
    buyer = Account.create()
    receipt = {
        "scheme": "x402-receipts/v0",
        "payment": {
            "chain_id": 8453,
            "tx_hash": TX,
            "asset": "USDC",
            "asset_address": TOKEN,
            "amount": "50000",
            "payer": buyer.address,
            "payee": seller.address,
        },
        "request": {
            "method": "GET",
            "url_hash": digest(URL.encode()),
            "params_hash": digest(PARAMS.encode()),
            "ts": "2026-10-13T00:00:00Z",
        },
        "response": {
            "status": 200,
            "body_sha256": digest(BODY),
            "content_type": "application/json",
            "ts": "2026-10-13T00:00:00.200Z",
            "latency_ms": 200,
        },
        "seller": {
            "erc8004_agent_id": "erc8004:8453:" + seller.address,
            "sig": "",
        },
        "buyer": {"countersig": None},
        "delivery": {"status": "delivered"},
    }
    domain, message, _ = _typed_receipt(receipt, True)
    signed = Account.sign_message(
        encode_typed_data(domain_data=domain, message_types=V03_TYPES, message_data=message),
        private_key=seller.key,
    )
    receipt["seller"]["sig"] = signed.signature.hex()
    return receipt, seller, buyer


def evidence_for(receipt, *, status="success", amount=None, tx=TX, confirmations=10):
    payment = receipt["payment"]
    transfer = {
        "transaction_hash": tx,
        "from": {"hash": payment["payer"]},
        "to": {"hash": payment["payee"]},
        "token": {"address_hash": TOKEN, "decimals": 6, "symbol": "USDC"},
        "total": {"value": amount if amount is not None else payment["amount"]},
    }
    return {
        "observation": {
            "chain_transaction": {
                "hash": tx,
                "status": status,
                "block_number": "0x64",
            },
            "token_transfers": {"items": [transfer]},
            "chain_rpc_observation": {"chain_id": "0x2105"},
        },
        "current_block": 0x64 + confirmations - 1,
        "source_url": "synthetic://test-only",
    }


def make_bundle(receipt, seller, body=BODY):
    return {
        "receipt": receipt,
        "response_body_base64": __import__("base64").b64encode(body).decode("ascii"),
        "expected_seller_address": seller.address,
        "expected_transaction_hash": TX,
        "expected_request_url": URL,
        "expected_request_method": "GET",
        "expected_params_json": PARAMS,
    }


class EvidenceBundleAuditTests(unittest.TestCase):
    def test_complete_matching_bundle_verifies_all_required_components(self):
        receipt, seller, _ = make_signed_receipt()
        result = audit_bundle(make_bundle(receipt, seller), chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["overall_verdict"], "VERIFIED")
        for key in ("seller_signature", "request_binding", "response_body_integrity", "signed_response_binding", "transaction_binding", "on_chain_settlement", "seller_signer_matches_payee"):
            self.assertEqual(result["components"][key]["verdict"], "VERIFIED", key)
        self.assertFalse(result["payment_submitted"])

    def test_tampered_response_bytes_fail_body_binding(self):
        receipt, seller, _ = make_signed_receipt()
        result = audit_bundle(make_bundle(receipt, seller, BODY + b"tampered"), chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["components"]["response_body_integrity"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["components"]["signed_response_binding"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["overall_verdict"], "NOT_VERIFIED")

    def test_wrong_expected_request_url_fails_request_binding(self):
        receipt, seller, _ = make_signed_receipt()
        bundle = make_bundle(receipt, seller)
        bundle["expected_request_url"] = "https://api.example.test/v1/other"
        result = audit_bundle(bundle, chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["components"]["request_binding"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["overall_verdict"], "NOT_VERIFIED")

    def test_wrong_expected_seller_signer_fails_signature(self):
        receipt, seller, other = make_signed_receipt()
        result = audit_bundle(make_bundle(receipt, other), chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["components"]["seller_signature"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["overall_verdict"], "NOT_VERIFIED")

    def test_wrong_expected_transaction_fails_transaction_binding(self):
        receipt, seller, _ = make_signed_receipt()
        bundle = make_bundle(receipt, seller)
        bundle["expected_transaction_hash"] = "0x" + "88" * 32
        result = audit_bundle(bundle, chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["components"]["transaction_binding"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["components"]["on_chain_settlement"]["verdict"], "NOT_VERIFIED")

    def test_wrong_onchain_amount_fails_settlement(self):
        receipt, seller, _ = make_signed_receipt()
        result = audit_bundle(make_bundle(receipt, seller), chain_loader=lambda tx: evidence_for(receipt, tx=tx, amount="50001"))
        self.assertEqual(result["components"]["on_chain_settlement"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["overall_verdict"], "NOT_VERIFIED")

    def test_unavailable_chain_evidence_remains_unknown(self):
        receipt, seller, _ = make_signed_receipt()
        def unavailable(_tx):
            raise RuntimeError("simulated unavailable read-only RPC")
        result = audit_bundle(make_bundle(receipt, seller), chain_loader=unavailable)
        self.assertEqual(result["components"]["seller_signature"]["verdict"], "VERIFIED")
        self.assertEqual(result["components"]["response_body_integrity"]["verdict"], "VERIFIED")
        self.assertEqual(result["components"]["on_chain_settlement"]["verdict"], "UNKNOWN")
        self.assertEqual(result["overall_verdict"], "UNKNOWN")

    def test_not_enough_confirmations_stays_unknown(self):
        receipt, seller, _ = make_signed_receipt()
        result = audit_bundle(make_bundle(receipt, seller), chain_loader=lambda tx: evidence_for(receipt, tx=tx, confirmations=1))
        self.assertEqual(result["components"]["on_chain_settlement"]["verdict"], "UNKNOWN")
        self.assertEqual(result["overall_verdict"], "UNKNOWN")

    def test_invalid_signature_is_not_verified(self):
        receipt, seller, _ = make_signed_receipt()
        receipt["seller"]["sig"] = "0x" + "00" * 65
        result = audit_bundle(make_bundle(receipt, seller), chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["components"]["seller_signature"]["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["overall_verdict"], "NOT_VERIFIED")

    def test_wrong_chain_is_not_claimed_as_verified(self):
        receipt, seller, _ = make_signed_receipt()
        receipt["payment"]["chain_id"] = 1
        result = audit_bundle(make_bundle(receipt, seller), chain_loader=lambda tx: evidence_for(receipt, tx=tx))
        self.assertEqual(result["components"]["on_chain_settlement"]["verdict"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
