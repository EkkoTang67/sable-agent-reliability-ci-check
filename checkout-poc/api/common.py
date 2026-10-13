"""Common helpers for Vercel Python functions; no secrets are exposed to browsers."""
from __future__ import annotations
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
for _path in (str(ROOT), str(SCRIPTS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from lib.paypal import CheckoutError, paypal_mode  # noqa: E402

MAX_BODY_BYTES = 16_384


def allowed_origins() -> set[str]:
    return {item.strip().rstrip("/") for item in os.getenv("SABLE_ALLOWED_ORIGINS", "").split(",") if item.strip()}


def origin_is_allowed(handler: BaseHTTPRequestHandler, *, allow_missing: bool = False) -> tuple[bool, str | None]:
    """Validate a browser Origin. Public, read-only config may omit Origin on same-origin GET.

    Browsers commonly omit Origin on same-origin GET/HEAD requests. That omission is
    not sufficient for mutating POST routes, which keep the strict default.
    """
    origin = handler.headers.get("Origin", "").strip().rstrip("/")
    if not origin:
        return (allow_missing, None)
    origins = allowed_origins()
    return bool(origins and origin in origins), origin or None


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any], origin: str | None = None) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store, max-age=0")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Referrer-Policy", "no-referrer")
    if origin and origin in allowed_origins():
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
    handler.end_headers()
    handler.wfile.write(body)


def method_not_allowed(handler: BaseHTTPRequestHandler, allowed: str) -> None:
    handler.send_response(405)
    handler.send_header("Allow", allowed)
    handler.send_header("Content-Length", "0")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_type = handler.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise CheckoutError(415, "UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json.")
    raw_length = handler.headers.get("Content-Length", "")
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise CheckoutError(400, "CONTENT_LENGTH_REQUIRED", "A valid Content-Length header is required.") from exc
    if length < 2 or length > MAX_BODY_BYTES:
        raise CheckoutError(413 if length > MAX_BODY_BYTES else 400, "REQUEST_SIZE_INVALID", "The request body must be between 2 bytes and 16 KB.")
    raw = handler.rfile.read(length)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckoutError(400, "INVALID_JSON", "The request body must be valid UTF-8 JSON.") from exc
    if not isinstance(value, dict):
        raise CheckoutError(400, "INVALID_JSON_SHAPE", "The request body must be a JSON object.")
    return value


def public_checkout_config() -> dict[str, Any]:
    client_id = os.getenv("PAYPAL_CLIENT_ID", "").strip()
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
    order_secret = os.getenv("SABLE_ORDER_HMAC_SECRET", "")
    origins = allowed_origins()
    try:
        mode = paypal_mode()
    except CheckoutError as exc:
        return {"enabled": False, "mode": os.getenv("PAYPAL_MODE", "sandbox"), "reason": exc.code}
    if not origins:
        return {"enabled": False, "mode": mode, "reason": "SABLE_ALLOWED_ORIGINS_NOT_CONFIGURED"}
    if not client_id or not client_secret or len(order_secret) < 32:
        return {"enabled": False, "mode": mode, "reason": "PAYPAL_OR_ORDER_SIGNING_NOT_CONFIGURED"}
    if mode == "live":
        required_flags = {
            "SABLE_SELLER_ELIGIBILITY_CONFIRMED": "false",
            "SABLE_POLICY_PAGES_APPROVED": "false",
            "SABLE_LIVE_REVIEW_APPROVED": "false",
        }
        missing_flags = [name for name, default in required_flags.items() if os.getenv(name, default).lower() != "true"]
        required_values = ("SABLE_SELLER_LEGAL_NAME", "SABLE_SUPPORT_EMAIL", "SABLE_TERMS_URL", "SABLE_REFUND_URL", "SABLE_PRIVACY_URL")
        missing_values = [name for name in required_values if not os.getenv(name, "").strip()]
        seller_name = os.getenv("SABLE_SELLER_LEGAL_NAME", "").strip()
        support_email = os.getenv("SABLE_SUPPORT_EMAIL", "").strip()
        policy_urls = [os.getenv(name, "").strip() for name in ("SABLE_TERMS_URL", "SABLE_REFUND_URL", "SABLE_PRIVACY_URL")]
        if seller_name and ("insert" in seller_name.lower() or "[" in seller_name or "]" in seller_name):
            missing_values.append("SABLE_SELLER_LEGAL_NAME_MUST_BE_REAL")
        if support_email and ("@" not in support_email or "insert" in support_email.lower()):
            missing_values.append("SABLE_SUPPORT_EMAIL_MUST_BE_VALID")
        if any(url and not url.startswith("https://") for url in policy_urls):
            missing_values.append("POLICY_URLS_MUST_USE_HTTPS")
        if origins and any(not origin.startswith("https://") for origin in origins):
            missing_values.append("LIVE_ORIGINS_MUST_USE_HTTPS")
        if missing_flags or missing_values:
            return {"enabled": False, "mode": mode, "reason": "LIVE_CHECKOUT_GATES_INCOMPLETE", "missing_configuration": missing_flags + missing_values}
    return {"enabled": True, "mode": mode, "client_id": client_id, "currency": "USD", "product_price": "9.00", "product_name": "SABLE x402 public evidence report"}
