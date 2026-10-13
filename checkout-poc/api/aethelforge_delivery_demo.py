"""Read-only verifier for Aethelforge's publicly documented signed-delivery demo.

Uses only the fixed published demo endpoint and public demo bearer token.
The token is documented by the site as a demonstration of access/identity policy;
it is NOT evidence of an x402 payment or on-chain settlement.
"""
from __future__ import annotations

import base64
import hashlib
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import rfc8785

from api.common import json_response, method_not_allowed, origin_is_allowed

DEMO_URL = "https://aethelforge.ai/api/receipts/sample"
JWK_URL = "https://aethelforge.ai/.well-known/aethelforge/keys"
DEMO_AUTH = "Bearer x402-demo-token"  # Publicly documented demo credential, not a secret.
MAX_RESPONSE_BYTES = 64 * 1024
TIMEOUT_SECONDS = 4.0


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch(url: str, *, authorization: str | None = None) -> tuple[int, dict[str, str], bytes, str]:
    headers = {
        "Accept": "application/json, application/jose, text/plain, */*",
        "User-Agent": "SABLE-read-only-receipt-demo/0.1",
        "Cache-Control": "no-cache",
    }
    if authorization:
        headers["Authorization"] = authorization
    request = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        # Capture bounded response evidence for explicit HTTP outcomes such as 402,
        # but never forward cookies or request credentials.
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raw = raw[:MAX_RESPONSE_BYTES]
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, raw, exc.geturl()
    with response:
        final_url = response.geturl()
        if urlsplit(final_url).hostname != urlsplit(url).hostname:
            raise ValueError("public demo redirected to a different host; refusing cross-host response")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("external demo response exceeded the 64 KB safety limit")
        return response.status, {k.lower(): v for k, v in response.headers.items()}, raw, final_url


def _post_json(url: str, payload: dict[str, Any]) -> tuple[int, Any]:
    """POST only a bounded JSON-RPC verification request to the fixed public MCP host."""
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SABLE-read-only-receipt-demo/0.1",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("MCP verifier response exceeded the 64 KB safety limit")
        try:
            value = json.loads(raw.decode("utf-8"))
        except Exception:
            value = {"unparsed": True}
        return exc.code, value
    with response:
        if urlsplit(response.geturl()).hostname != "aethelforge.ai":
            raise ValueError("MCP verifier redirected to a different host")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("MCP verifier response exceeded the 64 KB safety limit")
        return response.status, json.loads(raw.decode("utf-8"))


def _find_verifier_result(value: Any) -> bool | None:
    """Extract the issuer's explicit valid flag from a JSON-RPC/MCP tool response."""
    if isinstance(value, dict):
        if isinstance(value.get("valid"), bool):
            return value["valid"]
        if value.get("isError") is True:
            return False
        structured = value.get("structuredContent")
        found = _find_verifier_result(structured) if structured is not None else None
        if found is not None:
            return found
        content = value.get("content")
        found = _find_verifier_result(content) if content is not None else None
        if found is not None:
            return found
        for nested in value.values():
            if isinstance(nested, str) and nested.strip().startswith("{"):
                try:
                    found = _find_verifier_result(json.loads(nested))
                except Exception:
                    found = None
                if found is not None:
                    return found
            elif isinstance(nested, (dict, list)):
                found = _find_verifier_result(nested)
                if found is not None:
                    return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_verifier_result(nested)
            if found is not None:
                return found
    return None


def _local_verify_embedded_receipt(receipt: dict[str, Any], jwks: dict[str, Any]) -> dict[str, Any]:
    """Try exact, explicit JSON encodings locally with the published Ed25519 key."""
    payload = receipt.get("payload")
    kid = receipt.get("kid")
    if not isinstance(payload, dict) or not isinstance(kid, str) or not isinstance(receipt.get("signature"), str):
        return {"verdict": "NOT_VERIFIED", "reason": "Receipt is missing payload, kid, or signature."}
    keys = jwks.get("keys")
    matches = [item for item in keys if isinstance(item, dict) and item.get("kid") == kid] if isinstance(keys, list) else []
    if len(matches) != 1:
        return {"verdict": "UNKNOWN", "reason": "Receipt kid did not match exactly one published JWK."}
    jwk = matches[0]
    if jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519" or jwk.get("alg") != "EdDSA" or not isinstance(jwk.get("x"), str):
        return {"verdict": "NOT_VERIFIED", "reason": "Published JWK is not an Ed25519 signing key."}
    try:
        public_key = Ed25519PublicKey.from_public_bytes(_b64url_decode(jwk["x"]))
        signature = _b64url_decode(receipt["signature"])
    except Exception as exc:
        return {"verdict": "NOT_VERIFIED", "reason": f"Could not parse the published key or signature: {type(exc).__name__}."}

    candidates: list[tuple[str, bytes]] = []
    try:
        insertion_order = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        sorted_order = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical = rfc8785.dumps(payload)
        candidates.extend([
            ("compact_json_payload_insertion_order", insertion_order),
            ("compact_json_payload_sorted_keys", sorted_order),
            ("rfc8785_jcs_payload", canonical),
            ("sha256_compact_json_payload_insertion_order", hashlib.sha256(insertion_order).digest()),
            ("sha256_rfc8785_jcs_payload", hashlib.sha256(canonical).digest()),
        ])
        envelope = {"alg": receipt.get("alg"), "kid": kid, "payload": payload}
        envelope_insertion = json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        envelope_sorted = json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        candidates.extend([
            ("compact_json_envelope_alg_kid_payload", envelope_insertion),
            ("compact_json_envelope_sorted_keys", envelope_sorted),
            ("sha256_compact_json_envelope_alg_kid_payload", hashlib.sha256(envelope_insertion).digest()),
        ])
    except Exception as exc:
        return {"verdict": "UNKNOWN", "reason": f"Could not prepare local verification encodings: {type(exc).__name__}."}

    matching_methods: list[str] = []
    for name, message in candidates:
        try:
            public_key.verify(signature, message)
            matching_methods.append(name)
        except InvalidSignature:
            pass
        except Exception:
            pass
    if matching_methods:
        return {
            "verdict": "VERIFIED",
            "reason": "Ed25519 signature verified locally under the site's published public key.",
            "verification_source": "local cryptographic verification",
            "independent_verification": True,
            "matching_serializations": matching_methods,
            "kid": kid,
        }
    return {
        "verdict": "UNKNOWN",
        "reason": "The signature did not verify under the tested JSON encodings; no signing serialization is assumed.",
        "verification_source": "local cryptographic verification",
        "independent_verification": True,
        "tested_serializations": [name for name, _ in candidates],
        "kid": kid,
    }


def _verify_embedded_receipt(receipt: Any, jwks: Any, key_status: int) -> dict[str, Any]:
    """Use the issuer's public verify_receipt tool for its non-JWS receipt envelope."""
    if not isinstance(receipt, dict) or not isinstance(receipt.get("payload"), dict):
        return {"verdict": "NOT_VERIFIED", "reason": "Response receipt is not an object with a payload."}
    if receipt.get("alg") != "EdDSA" or not isinstance(receipt.get("kid"), str) or not isinstance(receipt.get("signature"), str):
        return {"verdict": "NOT_VERIFIED", "reason": "Embedded receipt is missing EdDSA algorithm, key ID, or signature."}
    if key_status != 200 or not isinstance(jwks, dict):
        return {"verdict": "UNKNOWN", "reason": f"Published JWKS unavailable or invalid (HTTP {key_status})."}
    keys = jwks.get("keys")
    matches = [item for item in keys if isinstance(item, dict) and item.get("kid") == receipt.get("kid")] if isinstance(keys, list) else []
    if len(matches) != 1:
        return {"verdict": "NOT_VERIFIED", "reason": "Receipt kid did not match exactly one published JWK.", "matching_jwk_count": len(matches)}
    local_signature = _local_verify_embedded_receipt(receipt, jwks)
    # Also ask the published verifier as corroboration; local verification remains separate.
    status, verifier_response = _post_json(
        "https://aethelforge.ai/mcp",
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "verify_receipt",
                "arguments": {"receipt": receipt},
            },
        },
    )
    valid = _find_verifier_result(verifier_response)
    if status != 200 or valid is None:
        return {
            "verdict": "UNKNOWN",
            "reason": "The publisher verifier did not return a recognized boolean verification result.",
            "issuer_verifier_http_status": status,
            "issuer_verifier_shape": sorted(verifier_response.keys()) if isinstance(verifier_response, dict) else type(verifier_response).__name__,
            "verification_source": "Aethelforge public MCP verify_receipt tool",
            "independent_verification": False,
            "payload": receipt.get("payload"),
            "kid": receipt.get("kid"),
            "local_signature_verification": local_signature,
        }
    issuer_verdict = "VERIFIED" if valid else "NOT_VERIFIED"
    if local_signature.get("verdict") == "VERIFIED":
        final_signature_verdict = "VERIFIED"
    elif issuer_verdict == "NOT_VERIFIED":
        final_signature_verdict = "NOT_VERIFIED"
    else:
        final_signature_verdict = "UNKNOWN"
    return {
        "verdict": final_signature_verdict,
        "reason": (
            "Both local Ed25519 verification and the publisher's public verify_receipt tool accepted the receipt."
            if local_signature.get("verdict") == "VERIFIED" and valid
            else "Local Ed25519 verification accepted the signature under the published key."
            if local_signature.get("verdict") == "VERIFIED"
            else "Only the publisher's public verifier accepted the receipt; local signature verification remains UNKNOWN."
            if valid
            else "The publisher's public verify_receipt tool rejected the receipt."
        ),
        "verification_source": "local Ed25519 check plus publisher MCP corroboration",
        "independent_verification": local_signature.get("verdict") == "VERIFIED",
        "issuer_verifier_http_status": status,
        "issuer_verifier_verdict": issuer_verdict if status == 200 and valid is not None else "UNKNOWN",
        "local_signature_verification": local_signature,
        "published_key_id_match": True,
        "protected_header": {"alg": receipt.get("alg"), "kid": receipt.get("kid")},
        "payload": receipt.get("payload"),
    }


def _b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=" for c in value):
        raise ValueError("invalid base64url field")
    clean = value.rstrip("=")
    return base64.urlsafe_b64decode(clean + "=" * ((4 - len(clean) % 4) % 4))


def _json_b64url(segment: str) -> dict[str, Any]:
    value = json.loads(_b64url_decode(segment).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JWS segment is not a JSON object")
    return value


def _find_compact_jws(headers: dict[str, str], body_obj: Any) -> tuple[str | None, str | None]:
    preferred = (
        "aethelforge-receipt",
        "x-aethelforge-receipt",
        "receipt",
        "x-receipt",
        "x-signed-receipt",
        "proof",
        "x-proof",
    )
    for name in preferred:
        val = headers.get(name)
        if isinstance(val, str) and val.count(".") == 2 and len(val) < 48_000:
            return name, val.strip()
    for name, val in headers.items():
        if "receipt" in name and isinstance(val, str) and val.count(".") == 2 and len(val) < 48_000:
            return name, val.strip()
    if isinstance(body_obj, dict):
        for key in ("receipt", "signed_receipt", "signedReceipt", "proof"):
            val = body_obj.get(key)
            if isinstance(val, str) and val.count(".") == 2 and len(val) < 48_000:
                return "body." + key, val.strip()
    return None, None


def _response_hash_claims(value: Any, prefix: str = "$") -> list[dict[str, str]]:
    names = {
        "body_sha256", "bodySha256", "body_hash", "bodyHash",
        "response_sha256", "responseSha256", "response_hash", "responseHash",
        "response_body_sha256", "responseBodySha256", "content_sha256", "contentSha256",
        "content_hash", "contentHash", "content_digest", "contentDigest",
    }
    generic_hash_names = {"sha256", "hash", "digest"}
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            response_context = any(marker in prefix.lower() for marker in (".response", ".body", ".content", ".resource"))
            if (key in names or (response_context and key.lower() in generic_hash_names)) and isinstance(nested, str):
                found.append({"path": prefix + "." + key, "value": nested})
            else:
                found.extend(_response_hash_claims(nested, prefix + "." + key))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found.extend(_response_hash_claims(nested, prefix + "[" + str(index) + "]"))
    return found[:20]


def _verify_jws(jws: str, jwks: Any) -> dict[str, Any]:
    pieces = jws.split(".")
    if len(pieces) != 3:
        return {"verdict": "NOT_VERIFIED", "reason": "Receipt is not a compact JWS with three segments."}
    try:
        protected = _json_b64url(pieces[0])
        payload = _json_b64url(pieces[1])
        signature = _b64url_decode(pieces[2])
    except Exception as exc:
        return {"verdict": "NOT_VERIFIED", "reason": f"JWS parsing failed: {type(exc).__name__}."}

    if protected.get("alg") != "EdDSA":
        return {"verdict": "NOT_VERIFIED", "reason": "The protected JWS alg is not EdDSA.", "protected_header": protected, "payload": payload}
    kid = protected.get("kid")
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    matching = [item for item in keys if isinstance(item, dict) and item.get("kid") == kid] if isinstance(keys, list) else []
    if len(matching) != 1:
        return {"verdict": "UNKNOWN", "reason": "The receipt kid did not resolve to exactly one key in the site's published JWKS.", "protected_header": protected, "payload": payload, "matching_jwk_count": len(matching)}
    jwk = matching[0]
    if jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519" or jwk.get("alg") != "EdDSA" or not isinstance(jwk.get("x"), str):
        return {"verdict": "NOT_VERIFIED", "reason": "Published JWKS key type/curve/algorithm is not an Ed25519 signing key.", "protected_header": protected, "payload": payload}
    try:
        public_bytes = _b64url_decode(jwk["x"])
        if len(public_bytes) != 32:
            raise ValueError("Ed25519 public key must be 32 bytes")
        Ed25519PublicKey.from_public_bytes(public_bytes).verify(signature, (pieces[0] + "." + pieces[1]).encode("ascii"))
    except (ValueError, InvalidSignature) as exc:
        return {"verdict": "NOT_VERIFIED", "reason": f"Ed25519 signature verification failed: {type(exc).__name__}.", "protected_header": protected, "payload": payload, "kid": kid}
    return {
        "verdict": "VERIFIED",
        "reason": "The receipt's compact JWS signature verifies under the matching key published by the demo site.",
        "protected_header": protected,
        "payload": payload,
        "kid": kid,
        "key_source": JWK_URL,
    }


def audit_demo() -> dict[str, Any]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        response_future = pool.submit(_fetch, DEMO_URL, authorization=DEMO_AUTH)
        jwks_future = pool.submit(_fetch, JWK_URL)
        status, headers, raw_body, final_url = response_future.result()
        key_status, key_headers, raw_jwks, key_url = jwks_future.result()

    try:
        body_text = raw_body.decode("utf-8")
        body_is_utf8 = True
    except UnicodeDecodeError:
        body_text = None
        body_is_utf8 = False
    try:
        body_obj = json.loads(body_text) if body_is_utf8 else None
    except json.JSONDecodeError:
        body_obj = None
    try:
        jwks = json.loads(raw_jwks.decode("utf-8")) if key_status == 200 else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        jwks = None

    body_sha = hashlib.sha256(raw_body).hexdigest()
    receipt_header, jws = _find_compact_jws(headers, body_obj)
    embedded_receipt = body_obj.get("receipt") if isinstance(body_obj, dict) and isinstance(body_obj.get("receipt"), dict) else None
    if status != 200:
        signature_result = {"verdict": "UNKNOWN", "reason": f"The public demo endpoint returned HTTP {status}, not 200."}
    elif jws is not None and (key_status != 200 or jwks is None):
        signature_result = {"verdict": "UNKNOWN", "reason": f"The demo's public JWKS was unavailable or invalid (HTTP {key_status})."}
    elif jws is not None:
        signature_result = _verify_jws(jws, jwks)
    elif embedded_receipt is not None:
        receipt_header = "body.receipt"
        signature_result = _verify_embedded_receipt(embedded_receipt, jwks, key_status)
    else:
        signature_result = {"verdict": "UNKNOWN", "reason": "The successful demo response did not expose a recognized signed receipt."}

    claims = signature_result.get("payload") if isinstance(signature_result.get("payload"), dict) else {}
    hash_claims = _response_hash_claims(claims)
    matching_hash_claims = [claim for claim in hash_claims if claim["value"].lower().removeprefix("sha256:") == body_sha]
    if signature_result.get("verdict") == "VERIFIED" and matching_hash_claims:
        body_verdict = {"verdict": "VERIFIED", "reason": "At least one hash claim inside the verified receipt equals SHA-256 of the exact raw HTTP response body.", "actual_body_sha256": body_sha, "matching_claims": matching_hash_claims}
    elif signature_result.get("verdict") == "VERIFIED" and hash_claims:
        body_verdict = {"verdict": "NOT_VERIFIED", "reason": "The verified receipt contains response hash claims, but none match SHA-256 of the exact raw HTTP response body.", "actual_body_sha256": body_sha, "declared_hash_claims": hash_claims}
    elif signature_result.get("verdict") == "VERIFIED" and not hash_claims:
        body_verdict = {"verdict": "NOT_VERIFIED", "reason": "The receipt signature is valid, but its signed payload contains no recognized response-body digest; it does not bind the full HTTP response bytes.", "actual_body_sha256": body_sha, "declared_hash_claims": []}
    else:
        body_verdict = {"verdict": "UNKNOWN", "reason": "A trusted receipt or recognized response-body digest claim was not available to compare against the exact raw bytes.", "actual_body_sha256": body_sha, "declared_hash_claims": hash_claims}

    # Aethelforge explicitly describes this fixed bearer token as a demo substitute for
    # identity/mandate/access policy, not an x402 payment. Never infer a chain settlement.
    return {
        "schema": "sable.public-signed-delivery-demo-audit.v1",
        "sample": "Aethelforge publicly documented signed-delivery demo",
        "source_url": DEMO_URL,
        "public_key_url": JWK_URL,
        "http_status": status,
        "response_final_url": final_url,
        "response_bytes": len(raw_body),
        "raw_response_sha256": body_sha,
        "raw_response_base64": base64.b64encode(raw_body).decode("ascii"),
        "raw_response_utf8": body_text,
        "receipt_transport": receipt_header,
        "receipt_jws": jws,
        "receipt_signature": signature_result,
        "body_binding": body_verdict,
        "settlement": {
            "verdict": "UNKNOWN",
            "reason": "The site documents this bearer as a demo access token standing in for identity/mandate/access authorization. This request did not submit an x402 payment or create a blockchain transaction.",
            "payment_submitted": False,
            "chain_transaction_hash": None,
        },
        # Overall intentionally remains UNKNOWN because this demo token is not a settlement proof.
        "signed_content_binding_verdict": (
            "VERIFIED" if signature_result.get("verdict") == "VERIFIED" and body_verdict.get("verdict") == "VERIFIED"
            else "NOT_VERIFIED" if signature_result.get("verdict") == "NOT_VERIFIED" or body_verdict.get("verdict") == "NOT_VERIFIED"
            else "UNKNOWN"
        ),
        "overall_verdict": "UNKNOWN",
        "limitations": [
            "This is an external demo-format check, not an x402 paid request or a real settlement proof.",
            "A valid site-published key establishes signature authenticity relative to that site, not independent truth of the receipt's claims.",
            "A matching body digest binds signed bytes; it does not prove semantic correctness or genuine computation.",
        ],
        "safe_response_headers": {
            key: value for key, value in headers.items()
            if key in {"content-type", "content-length", "cache-control", "date", "etag", "last-modified"}
            or "receipt" in key
        },
        "public_key_http_status": key_status,
        "public_key_source": key_url,
        "public_key_content_type": key_headers.get("content-type"),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This read-only demo is not approved for this Origin."}, origin)
            return
        try:
            result = audit_demo()
            json_response(self, 200, result, origin)
        except Exception as exc:
            json_response(self, 502, {"error": "SIGNED_DELIVERY_DEMO_UNAVAILABLE", "message": f"Read-only demo audit failed: {type(exc).__name__}. No payment was submitted."}, origin)

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        return
