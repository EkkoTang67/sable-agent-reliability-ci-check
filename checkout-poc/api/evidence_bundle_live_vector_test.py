"""Read-only live chain check for the public x402-receipts conformance vector.

This is intentionally separate from the deterministic no-network self-test. It checks
only a published historical Base USDC transaction; it does not call a paid resource,
create a wallet, or submit a transaction. Because the vector uses a vector-only signing
key and does not carry the original raw response bytes, the full delivery bundle remains
UNKNOWN even if the signature and on-chain settlement predicates pass.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from typing import Any

from api.common import json_response, method_not_allowed, origin_is_allowed
from api.evidence_bundle_audit import (
    _chain_evidence,
    _verify_seller_signature,
    _verify_settlement,
    _verdict,
)
from api.evidence_bundle_self_test import VECTOR_RECEIPT, VECTOR_SELLER

TX = "0xdeb5872c039a88ae37b66ae490c0c8da9b6a4c652d84494ddcc9a05211d6cc80"


def _run_live_vector_check() -> dict[str, Any]:
    receipt = VECTOR_RECEIPT
    signature = _verify_seller_signature(receipt, VECTOR_SELLER)
    try:
        evidence = _chain_evidence(TX)
        settlement = _verify_settlement(receipt, TX, evidence)
    except Exception as exc:
        settlement = _verdict(
            "UNKNOWN",
            "Read-only Base RPC evidence could not be obtained for the public vector.",
            error_type=type(exc).__name__,
        )

    payee = str(receipt["payment"]["payee"])
    signer_payee_matches = signature.get("verdict") == "VERIFIED" and (
        str(signature.get("recovered_signer", "")).lower() == payee.lower()
    )
    identity_result = _verdict(
        "VERIFIED" if signer_payee_matches else "NOT_VERIFIED",
        "This published conformance vector intentionally uses a vector-only signer that differs from payment.payee; it must not be treated as proof of the production seller's identity.",
        recovered_signer=signature.get("recovered_signer"),
        payment_payee=payee,
        vector_only_signer=VECTOR_SELLER,
    )

    chain_test_passed = (
        signature.get("verdict") == "VERIFIED"
        and settlement.get("verdict") == "VERIFIED"
    )
    return {
        "schema": "sable.x402.evidence-bundle-live-vector-test.v1",
        "test_mode": True,
        "sample_source": "StelarDigital/x402-receipts public pass-settled-delivered vector",
        "sample_transaction_hash": TX,
        "payment_required": False,
        "payment_submitted": False,
        "paid_endpoint_called": False,
        "chain_rpc_called": True,
        "seller_signature": signature,
        "seller_signer_matches_payment_payee": identity_result,
        "on_chain_settlement": settlement,
        "response_body_integrity": _verdict(
            "UNKNOWN",
            "The public vector supplies a body SHA-256 but not the original raw response bytes, so byte-for-byte delivery cannot be checked.",
            receipt_body_sha256=receipt["response"]["body_sha256"],
        ),
        "request_binding": _verdict(
            "UNKNOWN",
            "The public vector supplies request hashes but does not provide a sufficiently established exact historical request URL for this test.",
            receipt_url_hash=receipt["request"]["url_hash"],
            receipt_params_hash=receipt["request"]["params_hash"],
        ),
        "chain_test_passed": chain_test_passed,
        "overall_verdict": "UNKNOWN",
        "note": (
            "This is a read-only chain conformance check. Even if signature and settlement "
            "pass, the test-key identity mismatch and unavailable original response body "
            "mean the full delivery evidence bundle is not VERIFIED."
        ),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED"}, origin)
            return
        try:
            json_response(self, 200, _run_live_vector_check(), origin)
        except Exception as exc:
            json_response(
                self,
                200,
                {
                    "schema": "sable.x402.evidence-bundle-live-vector-test.v1",
                    "test_mode": True,
                    "payment_submitted": False,
                    "chain_rpc_called": True,
                    "chain_test_passed": False,
                    "overall_verdict": "UNKNOWN",
                    "error_type": type(exc).__name__,
                },
                origin,
            )

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        return
