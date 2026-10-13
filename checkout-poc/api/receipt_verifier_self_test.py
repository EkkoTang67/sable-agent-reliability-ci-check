"""Synthetic, no-payment self-test for the experimental x402ev/1 verifier."""
from __future__ import annotations

import base64
import hashlib
import json
from http.server import BaseHTTPRequestHandler

import rfc8785
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from api.common import json_response, method_not_allowed, origin_is_allowed
from scripts.sable_x402_execution_evidence import verify_execution_evidence

TX = "0x" + "44" * 32
PAYEE = "0x209693bc6afc0c5328ba36faf03c514ef312287c"
PAYER = "0x857b06519e91e3a54538791bdbb0e22373e36b66"
ASSET = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
NETWORK = "eip155:8453"
BODY = b'{"demo":"synthetic x402ev response"}'


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _synthetic_receipt():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    info = {
        "scheme": "x402ev/1",
        "canonicalization": "RFC8785",
        "payment": {
            "network": NETWORK,
            "txHash": TX,
            "payer": PAYER,
            "payee": PAYEE,
            "amount": "50000",
            "asset": ASSET,
        },
        "request": {
            "method": "GET",
            "urlHash": "sha256:" + ("1" * 64),
            "payloadHash": "sha256:" + ("2" * 64),
            "clientNonce": "synthetic-demo-nonce",
            "timestamp": 1791849600,
        },
        "delivery": {
            "statusCode": 200,
            "contentDigest": "sha256:" + hashlib.sha256(BODY).hexdigest(),
            "contentType": "application/json",
            "latencyMs": 1,
            "timestamp": 1791849601,
        },
        "signer": {"keyType": "Ed25519", "publicKey": _b64url(public_key)},
    }
    canonical_body = rfc8785.dumps(info)
    info["evidenceRef"] = "x402ev/1:sha256:" + hashlib.sha256(canonical_body).hexdigest()
    info["signer"]["signature"] = "base64url:" + _b64url(private_key.sign(canonical_body))
    receipt = {"extensions": {"execution-evidence": {"info": info}}}
    return receipt, _b64url(public_key)


def _run_self_test():
    receipt, trusted_key = _synthetic_receipt()
    good = verify_execution_evidence(
        receipt, BODY, trusted_public_key=trusted_key,
        expected_transaction_hash=TX, expected_network=NETWORK,
        expected_payee=PAYEE, expected_amount="0.05", expected_asset=ASSET,
        asset_decimals=6,
    )
    bad_body = verify_execution_evidence(
        receipt, BODY + b"tampered", trusted_public_key=trusted_key,
        expected_transaction_hash=TX, expected_network=NETWORK,
        expected_payee=PAYEE, expected_amount="0.05", expected_asset=ASSET,
        asset_decimals=6,
    )
    wrong_tx = verify_execution_evidence(
        receipt, BODY, trusted_public_key=trusted_key,
        expected_transaction_hash="0x" + "55" * 32, expected_network=NETWORK,
        expected_payee=PAYEE, expected_amount="0.05", expected_asset=ASSET,
        asset_decimals=6,
    )
    no_trust = verify_execution_evidence(
        receipt, BODY, trusted_public_key=None,
        expected_transaction_hash=TX, expected_network=NETWORK,
        expected_payee=PAYEE, expected_amount="0.05", expected_asset=ASSET,
        asset_decimals=6,
    )
    tests = [
        {"name": "valid signature + matching body + payment binding", "expected": "VERIFIED", "actual": good["verdict"]},
        {"name": "tampered response body", "expected": "NOT_VERIFIED", "actual": bad_body["verdict"]},
        {"name": "wrong expected transaction", "expected": "NOT_VERIFIED", "actual": wrong_tx["verdict"]},
        {"name": "missing external trust key", "expected": "UNKNOWN", "actual": no_trust["verdict"]},
    ]
    for item in tests:
        item["passed"] = item["actual"] == item["expected"]
    return {
        "test_mode": True,
        "synthetic": True,
        "payment_required": False,
        "chain_query_performed": False,
        "real_transaction_used": False,
        "verdict_scope": "receipt signature, response-body digest, and declared payment-field binding only",
        "does_not_prove": [
            "real payment settlement",
            "semantic correctness of response content",
            "genuine execution of computation",
            "independent witnessing",
            "authorized downstream state change",
        ],
        "tests": tests,
        "passed": all(item["passed"] for item in tests),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This demo origin is not approved."}, origin)
            return
        json_response(self, 200, _run_self_test(), origin)

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        return
