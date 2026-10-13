#!/usr/bin/env python3
"""Experimental x402ev/1 receipt verifier.

Implements the open x402-foundation execution-evidence proposal (#3682) on the
sandbox branch. It verifies receipt canonicalization, a server signature against
an externally pinned Ed25519 public key, response-body digest, and payment-field
binding. A VERIFIED result is limited to signed content-integrity evidence; it
does not prove semantic correctness, independent witnessing, real computation,
or an authorized downstream state transition.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
EVM_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SHA256_RE = re.compile(r"^sha256:([0-9a-f]{64})$")


def _decode_b64url(value: str, *, field: str, allow_prefix: bool = False) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty base64url string")
    encoded = value
    if allow_prefix and encoded.startswith("base64url:"):
        encoded = encoded[len("base64url:"):]
    if not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", encoded):
        raise ValueError(f"{field} is not valid base64url")
    encoded = encoded.rstrip("=")
    try:
        return base64.urlsafe_b64decode(encoded + "=" * ((4 - len(encoded) % 4) % 4))
    except Exception as exc:
        raise ValueError(f"{field} is not valid base64url") from exc


def _extract_info(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be a JSON object")
    if isinstance(receipt.get("info"), dict):
        return receipt["info"]
    ext = receipt.get("extensions")
    if isinstance(ext, dict):
        item = ext.get("execution-evidence")
        if isinstance(item, dict) and isinstance(item.get("info"), dict):
            return item["info"]
    item = receipt.get("execution-evidence")
    if isinstance(item, dict) and isinstance(item.get("info"), dict):
        return item["info"]
    if "evidenceRef" in receipt and "payment" in receipt:
        return receipt
    raise ValueError("could not find the x402 execution-evidence info object")


def _receipt_body(info: dict[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(info)
    body.pop("evidenceRef", None)
    body.pop("transparency", None)
    signer = body.get("signer")
    if isinstance(signer, dict):
        signer.pop("signature", None)
    return body


def _result(verdict: str, reason: str, **details: Any) -> dict[str, Any]:
    return {
        "schema": "sable.x402.execution-evidence-check.v1",
        "verdict": verdict,
        "reason": reason,
        **details,
        "limitations": [
            "This checks the server-signed content-binding claim against an externally pinned public key.",
            "It does not prove the content satisfies semantic acceptance criteria.",
            "It does not prove genuine compute execution, independent witnessing, or an authorized downstream state transition.",
            "It does not query chain finality; settlement must be verified separately.",
            "The public key's provenance must be established by the caller (for example, DNS, PKI, or a pre-established registry).",
        ],
    }


def verify_execution_evidence(
    receipt: Any,
    response_body: bytes | None,
    *,
    trusted_public_key: str | None,
    expected_transaction_hash: str,
    expected_network: str,
    expected_payee: str,
    expected_amount: str,
    expected_asset: str,
    asset_decimals: int = 6,
) -> dict[str, Any]:
    """Verify x402ev/1 receipt binding and body integrity without overclaiming."""
    try:
        info = _extract_info(receipt)
    except ValueError as exc:
        return _result("NOT_VERIFIED", str(exc), scope="receipt_structure")

    if info.get("scheme") != "x402ev/1":
        return _result("NOT_VERIFIED", "Receipt scheme is not x402ev/1.", scope="receipt_structure")
    if info.get("canonicalization") != "RFC8785":
        return _result("NOT_VERIFIED", "Receipt does not declare RFC8785 canonicalization.", scope="receipt_structure")

    payment = info.get("payment")
    request = info.get("request")
    delivery = info.get("delivery")
    signer = info.get("signer")
    if not all(isinstance(v, dict) for v in (payment, request, delivery, signer)):
        return _result("NOT_VERIFIED", "Receipt is missing a required payment, request, delivery, or signer object.", scope="receipt_structure")

    try:
        body = _receipt_body(info)
        canonical_body = rfc8785.dumps(body)
    except Exception as exc:
        return _result("NOT_VERIFIED", f"Receipt body cannot be RFC8785-canonicalized: {type(exc).__name__}.", scope="receipt_structure")

    calculated_ref = "x402ev/1:sha256:" + hashlib.sha256(canonical_body).hexdigest()
    if info.get("evidenceRef") != calculated_ref:
        return _result("NOT_VERIFIED", "evidenceRef does not match the canonical receipt body digest.", scope="receipt_integrity", calculated_evidence_ref=calculated_ref)

    content_digest = delivery.get("contentDigest")
    digest_match = SHA256_RE.fullmatch(content_digest) if isinstance(content_digest, str) else None
    if not digest_match:
        return _result("NOT_VERIFIED", "delivery.contentDigest must have the form sha256:<64 lowercase hex characters>.", scope="response_body_integrity")
    if response_body is None:
        return _result("UNKNOWN", "A response body file is required to recompute delivery.contentDigest.", scope="receipt_integrity", evidence_ref=calculated_ref, receipt_body_verified=True)
    if not isinstance(response_body, bytes):
        return _result("NOT_VERIFIED", "response_body must be raw response bytes.", scope="response_body_integrity")
    actual_digest = hashlib.sha256(response_body).hexdigest()
    if actual_digest != digest_match.group(1):
        return _result("NOT_VERIFIED", "Received response bytes do not match delivery.contentDigest.", scope="response_body_integrity", expected_digest=digest_match.group(1), actual_digest=actual_digest)

    tx_hash = payment.get("txHash")
    if not isinstance(tx_hash, str) or not TX_RE.fullmatch(tx_hash):
        return _result("UNKNOWN", "Receipt does not contain a valid payment.txHash.", scope="payment_binding", content_digest_verified=True)
    if not isinstance(expected_transaction_hash, str) or not TX_RE.fullmatch(expected_transaction_hash):
        return _result("NOT_VERIFIED", "The expected transaction hash provided to the verifier is invalid.", scope="payment_binding")
    if tx_hash.lower() != expected_transaction_hash.lower():
        return _result("NOT_VERIFIED", "Receipt is bound to a different transaction hash.", scope="payment_binding", receipt_transaction_hash=tx_hash)

    if payment.get("network") != expected_network:
        return _result("NOT_VERIFIED", "Receipt network does not match the expected network.", scope="payment_binding", receipt_network=payment.get("network"))
    payee = payment.get("payee")
    if not isinstance(payee, str) or not EVM_RE.fullmatch(payee):
        return _result("UNKNOWN", "Receipt does not contain a valid payment.payee.", scope="payment_binding")
    if payee.lower() != expected_payee.lower():
        return _result("NOT_VERIFIED", "Receipt payee does not match the expected recipient.", scope="payment_binding", receipt_payee=payee)
    payer = payment.get("payer")
    if not isinstance(payer, str) or not EVM_RE.fullmatch(payer):
        return _result("UNKNOWN", "Receipt does not contain a valid payment.payer.", scope="payment_binding")
    if payer.lower() == payee.lower():
        return _result("NOT_VERIFIED", "Receipt payer and payee must be distinct.", scope="payment_binding")
    asset = payment.get("asset")
    if not isinstance(asset, str) or asset.lower() != expected_asset.lower():
        return _result("NOT_VERIFIED", "Receipt asset does not match the expected token contract.", scope="payment_binding", receipt_asset=asset)
    try:
        expected_units = Decimal(str(expected_amount)) * (Decimal(10) ** asset_decimals)
        if not expected_units.is_finite() or expected_units != expected_units.to_integral_value():
            raise ValueError("expected amount cannot be represented at the configured token precision")
        expected_raw_amount = str(int(expected_units))
    except (InvalidOperation, ValueError, TypeError) as exc:
        return _result("NOT_VERIFIED", f"Expected amount is invalid: {exc}.", scope="payment_binding")
    if str(payment.get("amount", "")) != expected_raw_amount:
        return _result("NOT_VERIFIED", "Receipt atomic amount does not match the expected token amount.", scope="payment_binding", expected_atomic_amount=expected_raw_amount, receipt_atomic_amount=payment.get("amount"))

    method = request.get("method")
    if not isinstance(method, str) or not method:
        return _result("NOT_VERIFIED", "Receipt request.method is missing.", scope="receipt_structure")
    for field in ("urlHash", "payloadHash"):
        digest_value = request.get(field)
        if not isinstance(digest_value, str) or not SHA256_RE.fullmatch(digest_value):
            return _result("NOT_VERIFIED", f"Receipt request.{field} must have the form sha256:<64 lowercase hex characters>.", scope="receipt_structure")
    nonce = request.get("clientNonce")
    if not isinstance(nonce, str) or not 8 <= len(nonce) <= 64:
        return _result("NOT_VERIFIED", "Receipt request.clientNonce must be a string of 8 to 64 characters.", scope="receipt_structure")
    content_type = delivery.get("contentType")
    if not isinstance(content_type, str) or not content_type:
        return _result("NOT_VERIFIED", "Receipt delivery.contentType is missing.", scope="receipt_structure")
    latency = delivery.get("latencyMs")
    if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
        return _result("NOT_VERIFIED", "Receipt delivery.latencyMs must be a non-negative number.", scope="receipt_structure")

    status_code = delivery.get("statusCode")
    if not isinstance(status_code, int) or isinstance(status_code, bool) or status_code < 200 or status_code >= 300:
        return _result("NOT_VERIFIED", "Signed delivery status is not a successful 2xx HTTP response.", scope="delivery_claim", status_code=status_code)
    request_timestamp = request.get("timestamp")
    delivery_timestamp = delivery.get("timestamp")
    if (
        not isinstance(request_timestamp, (int, float)) or isinstance(request_timestamp, bool)
        or not isinstance(delivery_timestamp, (int, float)) or isinstance(delivery_timestamp, bool)
        or delivery_timestamp < request_timestamp
    ):
        return _result("NOT_VERIFIED", "Receipt request/delivery timestamps are missing or chronologically inconsistent.", scope="receipt_structure")

    signer_type = signer.get("keyType")
    signer_public_key = signer.get("publicKey")
    signature_value = signer.get("signature")
    if signer_type != "Ed25519" or not isinstance(signer_public_key, str) or not isinstance(signature_value, str):
        return _result("NOT_VERIFIED", "Receipt signer must provide an Ed25519 public key and signature.", scope="signature")
    try:
        receipt_public_key = _decode_b64url(signer_public_key, field="signer.publicKey")
    except ValueError as exc:
        return _result("NOT_VERIFIED", str(exc), scope="signature")
    if len(receipt_public_key) != 32:
        return _result("NOT_VERIFIED", "Ed25519 public keys must be 32 bytes.", scope="signature")

    if not trusted_public_key:
        return _result(
            "UNKNOWN",
            "Receipt structure and response digest match, but no externally pinned trusted public key was supplied.",
            scope="signed_content_binding_not_trusted",
            evidence_ref=calculated_ref,
            response_digest=actual_digest,
            content_digest_verified=True,
        )
    try:
        trusted_bytes = _decode_b64url(trusted_public_key, field="trusted_public_key")
    except ValueError as exc:
        return _result("NOT_VERIFIED", str(exc), scope="trust_input")
    if len(trusted_bytes) != 32:
        return _result("NOT_VERIFIED", "Trusted Ed25519 public key must be 32 bytes.", scope="trust_input")
    if trusted_bytes != receipt_public_key:
        return _result("NOT_VERIFIED", "Receipt signer key does not match the externally pinned trusted public key.", scope="trust_input")

    try:
        signature_bytes = _decode_b64url(signature_value, field="signer.signature", allow_prefix=True)
        Ed25519PublicKey.from_public_bytes(trusted_bytes).verify(signature_bytes, canonical_body)
    except (ValueError, InvalidSignature) as exc:
        return _result("NOT_VERIFIED", f"Ed25519 signature verification failed: {type(exc).__name__}.", scope="signature")

    return _result(
        "VERIFIED",
        "The pinned resource-server key signed a receipt binding the expected payment fields to response bytes whose SHA-256 digest matches.",
        scope="signed_content_integrity_and_payment_binding",
        evidence_ref=calculated_ref,
        response_digest=actual_digest,
        content_digest_verified=True,
        signature_verified=True,
        trusted_key_matched=True,
        receipt_transaction_hash=tx_hash,
        receipt_network=payment.get("network"),
        receipt_payee=payee,
        receipt_status_code=status_code,
        semantic_conformance="UNKNOWN",
        genuine_execution="UNKNOWN",
        independent_delivery_witness="UNKNOWN",
        settlement_finality_checked=False,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-json", required=True, help="x402ev/1 response evidence JSON")
    parser.add_argument("--body-file", required=True, help="Raw response-body bytes received from the service")
    parser.add_argument("--trusted-public-key", required=True, help="Externally pinned Ed25519 public key, base64url-encoded without a prefix")
    parser.add_argument("--expected-tx", required=True, help="Expected 0x-prefixed EVM transaction hash")
    parser.add_argument("--network", default="eip155:8453", help="Expected CAIP-2 network")
    parser.add_argument("--payee", required=True, help="Expected EVM payee address")
    parser.add_argument("--amount", required=True, help="Expected human-readable token amount, e.g. 0.05")
    parser.add_argument("--asset", required=True, help="Expected token contract address")
    parser.add_argument("--asset-decimals", type=int, default=6, help="Token decimal precision (default 6)")
    args = parser.parse_args(argv)
    try:
        receipt = json.loads(Path(args.receipt_json).read_text(encoding="utf-8"))
        body = Path(args.body_file).read_bytes()
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "NOT_VERIFIED", "reason": f"Could not load receipt/body input: {exc}"}), file=sys.stderr)
        return 2
    result = verify_execution_evidence(
        receipt, body, trusted_public_key=args.trusted_public_key,
        expected_transaction_hash=args.expected_tx, expected_network=args.network,
        expected_payee=args.payee, expected_amount=args.amount, expected_asset=args.asset,
        asset_decimals=args.asset_decimals,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "VERIFIED" else 1 if result["verdict"] == "NOT_VERIFIED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
