"""Tests for experimental x402ev/1 signed content-binding receipts."""
import base64
import hashlib
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rfc8785  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402
from sable_x402_execution_evidence import verify_execution_evidence  # noqa: E402

TX = "0x" + "4a" * 32
PAYEE = "0x209693bc6afc0c5328ba36faf03c514ef312287c"
PAYER = "0x857b06519e91e3a54538791bdbb0e22373e36b66"
ASSET = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
NETWORK = "eip155:8453"
BODY = b'{"data":"sample response","timestamp":"2026-10-13T00:00:00Z}'


def b64url(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def make_receipt(private_key=None, *, body=BODY, tx=TX):
    private_key = private_key or Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    info = {
        "scheme": "x402ev/1",
        "canonicalization": "RFC8785",
        "payment": {
            "network": NETWORK,
            "txHash": tx,
            "payer": PAYER,
            "payee": PAYEE,
            "amount": "50000",
            "asset": ASSET,
        },
        "request": {
            "method": "GET",
            "urlHash": "sha256:" + ("1" * 64),
            "payloadHash": "sha256:" + ("2" * 64),
            "clientNonce": "sample-nonce-20261013",
            "timestamp": 1791849600,
        },
        "delivery": {
            "statusCode": 200,
            "contentDigest": "sha256:" + hashlib.sha256(body).hexdigest(),
            "contentType": "application/json",
            "latencyMs": 42,
            "timestamp": 1791849601,
        },
        "signer": {"keyType": "Ed25519", "publicKey": b64url(public_key)},
    }
    canonical_body = rfc8785.dumps(info)
    info["evidenceRef"] = "x402ev/1:sha256:" + hashlib.sha256(canonical_body).hexdigest()
    signature = private_key.sign(canonical_body)
    info["signer"]["signature"] = "base64url:" + b64url(signature)
    return {"info": info}, b64url(public_key), private_key


class ExecutionEvidenceTests(unittest.TestCase):
    def verify(self, receipt, body=BODY, trusted=None, tx=TX):
        return verify_execution_evidence(
            receipt, body, trusted_public_key=trusted,
            expected_transaction_hash=tx, expected_network=NETWORK,
            expected_payee=PAYEE, expected_amount="0.05",
            expected_asset=ASSET, asset_decimals=6,
        )

    def test_valid_signature_body_digest_and_payment_binding(self):
        receipt, key, _ = make_receipt()
        result = self.verify(receipt, trusted=key)
        self.assertEqual(result["verdict"], "VERIFIED")
        self.assertTrue(result["signature_verified"])
        self.assertTrue(result["content_digest_verified"])
        self.assertEqual(result["semantic_conformance"], "UNKNOWN")
        self.assertEqual(result["settlement_finality_checked"], False)

    def test_changed_body_is_rejected(self):
        receipt, key, _ = make_receipt()
        result = self.verify(receipt, body=BODY + b"tampered", trusted=key)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["scope"], "response_body_integrity")

    def test_missing_trusted_key_does_not_trust_receipt_self_asserted_key(self):
        receipt, _, _ = make_receipt()
        result = self.verify(receipt, trusted=None)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("externally pinned trusted public key", result["reason"])

    def test_wrong_trusted_key_is_rejected(self):
        receipt, _, _ = make_receipt()
        _, wrong_key, _ = make_receipt()
        result = self.verify(receipt, trusted=wrong_key)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["scope"], "trust_input")

    def test_receipt_for_different_transaction_is_rejected(self):
        different_tx = "0x" + "5b" * 32
        receipt, key, _ = make_receipt(tx=different_tx)
        result = self.verify(receipt, trusted=key)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["scope"], "payment_binding")

    def test_tampered_signed_fields_are_rejected(self):
        receipt, key, _ = make_receipt()
        receipt["info"]["payment"]["amount"] = "50001"
        result = self.verify(receipt, trusted=key)
        self.assertEqual(result["verdict"], "NOT_VERIFIED")
        self.assertEqual(result["scope"], "receipt_integrity")


if __name__ == "__main__":
    unittest.main()
