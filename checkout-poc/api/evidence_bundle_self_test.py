"""No-payment synthetic test of the deployed evidence-bundle verifier."""
from __future__ import annotations

import base64
import hashlib
from http.server import BaseHTTPRequestHandler
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data

from api.common import json_response, method_not_allowed, origin_is_allowed
from api.evidence_bundle_audit import V03_TYPES, _typed_receipt, _verify_seller_signature, audit_bundle

TX = "0x" + "77" * 32
TOKEN = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
URL = "https://synthetic.invalid/v1/result?kind=demo"
PARAMS = "{}"
BODY = b'{"status":"complete","value":42}'

# Public conformance fixture from StelarDigital/x402-receipts vectors/pass-settled-delivered.json.
# This vector uses a vector-only seller key by design; the expected signer intentionally
# differs from payment.payee. Only its signature is checked here, not its body or settlement.
VECTOR_SELLER = "0xC49Adc1ef48fC1D237d55379Fef7F3142cE22468"
VECTOR_RECEIPT = {
    "scheme": "x402-receipts/v0",
    "payment": {
        "chain_id": 8453,
        "tx_hash": "0xdeb5872c039a88ae37b66ae490c0c8da9b6a4c652d84494ddcc9a05211d6cc80",
        "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "asset_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "amount": "5000",
        "payer": "0xe61Bd34fcEdF14E0b41B582166eed69E3a6deF89",
        "payee": "0x32d711C66dD1AD0c42D0cFe48e58ee5f2dE7c243",
    },
    "request": {
        "method": "GET",
        "url_hash": "84d14f74996f93224e9e9db28ff4a39b5cc45b443486a3bb2c5bf0f3546ab7d8",
        "params_hash": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
        "ts": "2026-07-11T21:03:55Z",
        "payment_requirements_sha256": "40f3423d4e602c7324d45d51cd273fb238266ee08fef7d9ace34132a7a9b5a2c",
    },
    "response": {
        "status": 200,
        "body_sha256": "5545e4424324ee42fd5b739544f462a47b81f122b02ec859af986e9316fadee4",
        "content_type": "application/json",
        "ts": "2026-07-11T21:03:55Z",
        "latency_ms": 296,
    },
    "seller": {
        "erc8004_agent_id": "erc8004:8453:0x32d711C66dD1AD0c42D0cFe48e58ee5f2dE7c243",
        "sig": "0xcb4387fd51ca75996b20430239086803a8e88de8fa378acbfb95b2a384ffbe240e592d8d724fa9f5935465b791aa57fcb16563f25fe7e450adc2d6e512a2a73c1b",
    },
}


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _make_receipt():
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
            "url_hash": _digest(URL.encode("utf-8")),
            "params_hash": _digest(PARAMS.encode("utf-8")),
            "ts": "2026-10-13T00:00:00Z",
        },
        "response": {
            "status": 200,
            "body_sha256": _digest(BODY),
            "content_type": "application/json",
            "ts": "2026-10-13T00:00:00.200Z",
            "latency_ms": 200,
        },
        "seller": {"erc8004_agent_id": "erc8004:8453:" + seller.address, "sig": ""},
        "buyer": {"countersig": None},
        "delivery": {"status": "delivered"},
    }
    domain, message, _primary_type = _typed_receipt(receipt, True)
    signable = encode_typed_data(domain_data=domain, message_types=V03_TYPES, message_data=message)
    signed = Account.sign_message(signable, private_key=seller.key)
    signature_hex = signed.signature.hex()
    receipt["seller"]["sig"] = signature_hex if signature_hex.startswith("0x") else "0x" + signature_hex
    return receipt, seller


def _evidence_for(receipt: dict[str, Any], *, amount: str | None = None, status: str = "success", confirmations: int = 4):
    payment = receipt["payment"]
    transfer = {
        "transaction_hash": TX,
        "from": {"hash": payment["payer"]},
        "to": {"hash": payment["payee"]},
        "token": {"address_hash": TOKEN, "decimals": 6, "symbol": "USDC"},
        "total": {"value": amount if amount is not None else payment["amount"]},
    }
    return {
        "observation": {
            "chain_transaction": {"hash": TX, "status": status, "block_number": "0x64"},
            "token_transfers": {"items": [transfer]},
        },
        "current_block": 0x64 + confirmations - 1,
        "source_url": "synthetic://not-a-real-rpc",
    }


def _bundle(receipt, seller, raw_body=BODY):
    return {
        "receipt": receipt,
        "response_body_base64": base64.b64encode(raw_body).decode("ascii"),
        "expected_seller_address": seller.address,
        "expected_transaction_hash": TX,
        "expected_request_url": URL,
        "expected_request_method": "GET",
        "expected_params_json": PARAMS,
    }


def _run_tests() -> dict[str, Any]:
    tests = []
    receipt, seller = _make_receipt()

    good = audit_bundle(_bundle(receipt, seller), chain_loader=lambda tx: _evidence_for(receipt))
    tests.append({
        "name": "valid EIP-712 seller signature + exact body + exact request + matching settlement",
        "expected": "VERIFIED",
        "actual": good["overall_verdict"],
        "component_results": {key: value["verdict"] for key, value in good["components"].items()},
        "signature_detail": good["components"]["seller_signature"],
        "request_detail": good["components"]["request_binding"],
        "body_detail": good["components"]["response_body_integrity"],
        "settlement_detail": good["components"]["on_chain_settlement"],
    })

    vector_result = _verify_seller_signature(VECTOR_RECEIPT, VECTOR_SELLER)
    tests.append({
        "name": "upstream public x402-receipts v0.3 signature conformance vector",
        "expected": "VERIFIED",
        "actual": vector_result["verdict"],
        "signature_detail": vector_result,
    })

    tampered = audit_bundle(_bundle(receipt, seller, BODY + b"tampered"), chain_loader=lambda tx: _evidence_for(receipt))
    tests.append({
        "name": "tampered raw response bytes",
        "expected": "NOT_VERIFIED",
        "actual": tampered["overall_verdict"],
    })

    wrong_request = _bundle(receipt, seller)
    wrong_request["expected_request_url"] = "https://synthetic.invalid/v1/other"
    request_result = audit_bundle(wrong_request, chain_loader=lambda tx: _evidence_for(receipt))
    tests.append({
        "name": "wrong expected request URL",
        "expected": "NOT_VERIFIED",
        "actual": request_result["overall_verdict"],
    })

    wrong_tx = _bundle(receipt, seller)
    wrong_tx["expected_transaction_hash"] = "0x" + "88" * 32
    tx_result = audit_bundle(wrong_tx, chain_loader=lambda tx: _evidence_for(receipt))
    tests.append({
        "name": "wrong expected transaction hash",
        "expected": "NOT_VERIFIED",
        "actual": tx_result["overall_verdict"],
    })

    def unavailable(_tx):
        raise RuntimeError("synthetic no-RPC-evidence case")
    no_chain = audit_bundle(_bundle(receipt, seller), chain_loader=unavailable)
    tests.append({
        "name": "missing chain evidence",
        "expected": "UNKNOWN",
        "actual": no_chain["overall_verdict"],
    })

    for item in tests:
        item["passed"] = item["actual"] == item["expected"]
    return {
        "schema": "sable.x402.evidence-bundle-self-test.v1",
        "test_mode": True,
        "synthetic": True,
        "payment_required": False,
        "payment_submitted": False,
        "chain_rpc_called": False,
        "note": "All keys, receipts, body bytes, and settlement observations are generated in-memory. This tests verifier logic only, not a real buyer transaction.",
        "tests": tests,
        "passed": all(item["passed"] for item in tests),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED"}, origin)
            return
        try:
            json_response(self, 200, _run_tests(), origin)
        except Exception as exc:
            json_response(self, 500, {
                "schema": "sable.x402.evidence-bundle-self-test.v1",
                "test_mode": True,
                "passed": False,
                "error": type(exc).__name__,
            }, origin)

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        return
