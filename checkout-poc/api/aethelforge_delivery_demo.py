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
    }
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in names and isinstance(nested, str):
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
    if status != 200:
        signature_result = {"verdict": "UNKNOWN", "reason": f"The public demo endpoint returned HTTP {status}, not 200."}
    elif jws is None:
        signature_result = {"verdict": "UNKNOWN", "reason": "The successful demo response did not expose a compact JWS receipt in a recognized response header or top-level JSON field."}
    elif key_status != 200 or jwks is None:
        signature_result = {"verdict": "UNKNOWN", "reason": f"The demo's public JWKS was unavailable or invalid (HTTP {key_status})."}
    else:
        signature_result = _verify_jws(jws, jwks)

    claims = signature_result.get("payload") if isinstance(signature_result.get("payload"), dict) else {}
    hash_claims = _response_hash_claims(claims)
    matching_hash_claims = [claim for claim in hash_claims if claim["value"].lower().removeprefix("sha256:") == body_sha]
    if signature_result.get("verdict") == "VERIFIED" and matching_hash_claims:
        body_verdict = {"verdict": "VERIFIED", "reason": "At least one hash claim inside the valid signed receipt equals SHA-256 of the exact raw HTTP response body.", "actual_body_sha256": body_sha, "matching_claims": matching_hash_claims}
    elif signature_result.get("verdict") == "VERIFIED" and hash_claims:
        body_verdict = {"verdict": "NOT_VERIFIED", "reason": "The signed receipt contains response hash claims, but none match SHA-256 of the exact raw HTTP response body.", "actual_body_sha256": body_sha, "declared_hash_claims": hash_claims}
    else:
        body_verdict = {"verdict": "UNKNOWN", "reason": "A trusted, recognizable response-body digest claim was not available to compare against the exact raw bytes.", "actual_body_sha256": body_sha, "declared_hash_claims": hash_claims}

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
        "receipt_signature": signature_result,
        "body_binding": body_verdict,
        "settlement": {
            "verdict": "UNKNOWN",
            "reason": "The site documents this bearer as a demo access token standing in for identity/mandate/access authorization. This request did not submit an x402 payment or create a blockchain transaction.",
            "payment_submitted": False,
            "chain_transaction_hash": None,
        },
        "overall_verdict": "VERIFIED" if signature_result.get("verdict") == "VERIFIED" and body_verdict.get("verdict") == "VERIFIED" else "UNKNOWN",
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
