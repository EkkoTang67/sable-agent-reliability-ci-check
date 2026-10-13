"""PayPal Orders v2 helpers for a sandbox-first, one-report checkout.

No function in this module creates a live transaction unless the caller has set
PAYPAL_MODE=live and PAYPAL_LIVE_ENABLED=true. Never store the API secret in a
public variable or commit it to source control.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
EVM_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
ORDER_RE = re.compile(r"^[A-Z0-9-]{10,64}$")
ENDPOINT_RE = re.compile(r"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]{1,190}$")
FIXED_PRICE_USD = "9.00"
# Circle-published native USDC contract on Base mainnet. This prototype intentionally
# rejects other assets/networks rather than risk symbol-only token matching.
BASE_NATIVE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
PRODUCT_DESCRIPTION = "SABLE x402 public evidence report"
CUSTOM_ID_PREFIX = "SABLE-X402-V1"


class CheckoutError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def paypal_mode() -> str:
    mode = os.getenv("PAYPAL_MODE", "sandbox").strip().lower()
    if mode not in {"sandbox", "live"}:
        raise CheckoutError(503, "PAYPAL_MODE_INVALID", "PAYPAL_MODE must be sandbox or live.")
    if mode == "live" and os.getenv("PAYPAL_LIVE_ENABLED", "false").lower() != "true":
        raise CheckoutError(503, "LIVE_CHECKOUT_LOCKED", "Live checkout is disabled until seller eligibility and production configuration are confirmed.")
    return mode


def paypal_base_url() -> str:
    return "https://api-m.sandbox.paypal.com" if paypal_mode() == "sandbox" else "https://api-m.paypal.com"


def hmac_secret() -> bytes:
    secret = os.getenv("SABLE_ORDER_HMAC_SECRET", "")
    if len(secret) < 32:
        raise CheckoutError(503, "ORDER_SIGNING_NOT_CONFIGURED", "SABLE_ORDER_HMAC_SECRET must be configured with at least 32 characters.")
    return secret.encode("utf-8")


def canonical_case(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise CheckoutError(400, "INVALID_CASE", "Expected a JSON object containing the report inputs.")

    tx_hash = str(payload.get("transaction_hash", "")).strip()
    if not TX_RE.fullmatch(tx_hash):
        raise CheckoutError(400, "INVALID_TRANSACTION_HASH", "transaction_hash must be a 0x-prefixed 32-byte transaction hash.")

    slug = str(payload.get("slug", "")).strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise CheckoutError(400, "INVALID_SERVICE_SLUG", "slug must contain only lowercase letters, digits, and hyphens.")

    recipient = str(payload.get("recipient", "")).strip()
    if not EVM_RE.fullmatch(recipient):
        raise CheckoutError(400, "INVALID_RECIPIENT", "recipient must be a valid 20-byte EVM address.")

    amount_raw = str(payload.get("expected_amount", "")).strip()
    # Reject exponent notation and absurd decimal precision to avoid unexpectedly huge
    # formatting work and to match the visible HTML form contract.
    if len(amount_raw) > 40 or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,18})?", amount_raw):
        raise CheckoutError(400, "INVALID_AMOUNT", "expected_amount must be a plain positive decimal with at most 18 decimal places.")
    try:
        amount = Decimal(amount_raw)
    except InvalidOperation as exc:
        raise CheckoutError(400, "INVALID_AMOUNT", "expected_amount must be a positive decimal amount.") from exc
    if not amount.is_finite() or amount <= 0 or amount > Decimal("100000000") or len(amount.as_tuple().digits) > 24:
        raise CheckoutError(400, "INVALID_AMOUNT", "expected_amount is outside the supported range.")
    amount_text = format(amount.normalize(), "f")
    if "." in amount_text:
        amount_text = amount_text.rstrip("0").rstrip(".")

    asset = str(payload.get("asset", "USDC")).strip().upper()
    if asset != "USDC":
        raise CheckoutError(400, "UNSUPPORTED_ASSET", "This prototype supports native USDC on Base only.")

    endpoint = str(payload.get("endpoint", "")).strip()
    if not ENDPOINT_RE.fullmatch(endpoint) or endpoint.startswith("//") or ".." in endpoint or "\\" in endpoint:
        raise CheckoutError(400, "INVALID_ENDPOINT", "endpoint must be a safe absolute path, not a URL or traversal path.")

    network = str(payload.get("network", "eip155:8453")).strip()
    # The collector in this prototype queries Base Blockscout only.
    if network != "eip155:8453":
        raise CheckoutError(400, "UNSUPPORTED_NETWORK", "This prototype supports Base mainnet only (eip155:8453).")

    return {
        "transaction_hash": tx_hash.lower(),
        "slug": slug,
        "recipient": recipient.lower(),
        "expected_amount": amount_text,
        "asset": asset,
        "asset_contract": BASE_NATIVE_USDC,
        "endpoint": endpoint,
        "network": network,
    }


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_case(case: dict[str, str]) -> str:
    """Bind the immutable evidence inputs to the PayPal order using custom_id."""
    case_digest = hashlib.sha256(canonical_json(case)).hexdigest()
    signature = hmac.new(hmac_secret(), case_digest.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    custom_id = f"{CUSTOM_ID_PREFIX}:{case_digest}:{signature}"
    if len(custom_id) > 127:
        raise CheckoutError(500, "CUSTOM_ID_TOO_LONG", "Internal order reference exceeds provider limit.")
    return custom_id


def verify_case_signature(case: dict[str, str], custom_id: Any) -> bool:
    if not isinstance(custom_id, str):
        return False
    match = re.fullmatch(rf"{CUSTOM_ID_PREFIX}:([0-9a-f]{{64}}):([0-9a-f]{{32}})", custom_id)
    if not match:
        return False
    case_digest, provided_sig = match.groups()
    actual_digest = hashlib.sha256(canonical_json(case)).hexdigest()
    expected_sig = hmac.new(hmac_secret(), case_digest.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(case_digest, actual_digest) and hmac.compare_digest(provided_sig, expected_sig)


def _request_json(url: str, *, method: str, headers: dict[str, str], body: bytes | None = None, timeout: float = 5) -> dict[str, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise CheckoutError(502, "PROVIDER_RESPONSE_TOO_LARGE", "Payment provider response exceeded the safety limit.")
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise CheckoutError(502, "PROVIDER_RESPONSE_INVALID", "Payment provider returned an unexpected response shape.")
            return value
    except urllib.error.HTTPError as exc:
        # Show only allow-listed PayPal diagnostic fields; never return raw provider
        # bodies or credential material to the browser.
        raw_error = ""
        try:
            raw_error = exc.read(1200).decode("utf-8", errors="replace")
        except Exception:
            pass
        safe_name = ""
        safe_issue = ""
        safe_debug_id = ""
        try:
            error_doc = json.loads(raw_error) if raw_error else {}
            if isinstance(error_doc, dict):
                candidate = error_doc.get("name") or error_doc.get("error") or ""
                if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", candidate):
                    safe_name = candidate
                details = error_doc.get("details")
                if isinstance(details, list) and details and isinstance(details[0], dict):
                    issue = details[0].get("issue", "")
                    if isinstance(issue, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", issue):
                        safe_issue = issue
                debug_id = error_doc.get("debug_id", "")
                if isinstance(debug_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", debug_id):
                    safe_debug_id = debug_id
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        if url.endswith("/v1/oauth2/token"):
            stage = "PayPal Sandbox authentication"
        else:
            stage = "PayPal order API"
        suffix = f", {safe_name}" if safe_name else ""
        suffix += f", issue={safe_issue}" if safe_issue else ""
        suffix += f", debug_id={safe_debug_id}" if safe_debug_id else ""
        advice = " Verify the Client ID and Secret are from the same Sandbox app." if exc.code in {400, 401, 403} else ""
        raise CheckoutError(502, "PAYPAL_API_ERROR", f"{stage} rejected the request (HTTP {exc.code}{suffix}).{advice}") from exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise CheckoutError(502, "PAYPAL_API_UNAVAILABLE", f"Payment provider request failed: {type(exc).__name__}") from exc


def paypal_api_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    client_id = os.getenv("PAYPAL_CLIENT_ID", "").strip()
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise CheckoutError(503, "PAYPAL_NOT_CONFIGURED", "PayPal API credentials are not configured.")

    base = paypal_base_url()
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    token_payload = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("ascii")
    token_response = _request_json(
        f"{base}/v1/oauth2/token",
        method="POST",
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        body=token_payload,
    )
    access_token = token_response.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise CheckoutError(502, "PAYPAL_TOKEN_MISSING", "PayPal did not return an access token.")

    data = canonical_json(payload) if payload is not None else None
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json", "Content-Type": "application/json", "Prefer": "return=representation"}
    if method.upper() == "POST":
        request_material = path
        if not path.endswith("/refund"):
            request_material += data.decode("utf-8", errors="ignore") if data else ""
        headers["PayPal-Request-Id"] = hashlib.sha256(request_material.encode("utf-8")).hexdigest()[:32]
    return _request_json(f"{base}{path}", method=method.upper(), headers=headers, body=data)


def create_order(
    case: dict[str, str],
    api_call: Callable[..., dict[str, Any]] | None = None,
    *,
    return_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, str]:
    """Create a fixed-price order and return only a validated PayPal approval link."""
    if bool(return_url) != bool(cancel_url):
        raise CheckoutError(400, "RETURN_URL_PAIR_REQUIRED", "Both return_url and cancel_url must be supplied together.")
    call = api_call or paypal_api_request
    mode = paypal_mode()
    signed_custom_id = sign_case(case)
    payload: dict[str, Any] = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "custom_id": signed_custom_id,
            "description": PRODUCT_DESCRIPTION,
            "amount": {"currency_code": "USD", "value": FIXED_PRICE_USD, "breakdown": {"item_total": {"currency_code": "USD", "value": FIXED_PRICE_USD}}},
            "items": [{"name": "SABLE x402 public evidence report", "quantity": "1", "unit_amount": {"currency_code": "USD", "value": FIXED_PRICE_USD}, "category": "DIGITAL_GOODS"}],
        }],
    }
    if return_url and cancel_url:
        payload["payment_source"] = {
            "paypal": {
                "experience_context": {
                    "brand_name": "SABLE",
                    "landing_page": "LOGIN",
                    "user_action": "PAY_NOW",
                    "shipping_preference": "NO_SHIPPING",
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                }
            }
        }
    else:
        # Backward-compatible SDK flow for older preview pages.
        payload["application_context"] = {
            "brand_name": "SABLE",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "shipping_preference": "NO_SHIPPING",
        }

    response = call("POST", "/v2/checkout/orders", payload)
    order_id = response.get("id")
    if not isinstance(order_id, str) or not ORDER_RE.fullmatch(order_id):
        raise CheckoutError(502, "PAYPAL_ORDER_ID_MISSING", "PayPal did not return a valid order ID.")
    if response.get("status") not in {"CREATED", "PAYER_ACTION_REQUIRED", "APPROVED", "COMPLETED"}:
        raise CheckoutError(502, "PAYPAL_ORDER_STATUS_UNEXPECTED", "PayPal returned an unexpected order status.")

    approval_url = ""
    links = response.get("links")
    allowed_hosts = {"www.sandbox.paypal.com", "sandbox.paypal.com"} if mode == "sandbox" else {"www.paypal.com", "paypal.com"}
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict) or link.get("rel") not in {"approve", "payer-action"}:
                continue
            href = link.get("href")
            if not isinstance(href, str):
                continue
            parsed = urllib.parse.urlsplit(href)
            if (
                parsed.scheme == "https"
                and parsed.hostname in allowed_hosts
                and parsed.path.rstrip("/") == "/checkoutnow"
                and not parsed.username
                and not parsed.password
            ):
                approval_url = href
                break
    return {"orderID": order_id, "mode": mode, "approvalUrl": approval_url}


def extract_purchase_unit(order: dict[str, Any]) -> dict[str, Any]:
    units = order.get("purchase_units")
    if not isinstance(units, list) or len(units) != 1 or not isinstance(units[0], dict):
        raise CheckoutError(400, "ORDER_CONTENT_MISMATCH", "The PayPal order does not match the expected single-product purchase.")
    return units[0]


def _completed_capture(order: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    unit = extract_purchase_unit(order)
    payments = unit.get("payments")
    captures = payments.get("captures") if isinstance(payments, dict) else None
    if not isinstance(captures, list):
        return None
    for capture in captures:
        if isinstance(capture, dict) and capture.get("status") == "COMPLETED" and isinstance(capture.get("id"), str):
            return capture["id"], capture
    return None


def validate_order(order: dict[str, Any], case: dict[str, str], expected_order_id: str) -> None:
    if order.get("id") != expected_order_id:
        raise CheckoutError(400, "ORDER_ID_MISMATCH", "The PayPal order ID does not match the request.")
    if order.get("intent") != "CAPTURE":
        raise CheckoutError(400, "ORDER_INTENT_MISMATCH", "Only capture-intent PayPal orders are supported.")
    unit = extract_purchase_unit(order)
    if unit.get("description") != PRODUCT_DESCRIPTION or not verify_case_signature(case, unit.get("custom_id")):
        raise CheckoutError(400, "ORDER_CONTENT_MISMATCH", "The order does not match the original signed report request.")
    amount = unit.get("amount")
    if not isinstance(amount, dict) or amount.get("currency_code") != "USD" or amount.get("value") != FIXED_PRICE_USD:
        raise CheckoutError(400, "ORDER_AMOUNT_MISMATCH", "The PayPal order amount does not match the configured price.")
    items = unit.get("items")
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
        raise CheckoutError(400, "ORDER_ITEMS_MISMATCH", "The order must contain exactly one report item.")
    item = items[0]
    if item.get("name") != "SABLE x402 public evidence report" or str(item.get("quantity")) != "1":
        raise CheckoutError(400, "ORDER_ITEMS_MISMATCH", "The order item is not the expected report product.")
    unit_amount = item.get("unit_amount")
    if not isinstance(unit_amount, dict) or unit_amount.get("currency_code") != "USD" or unit_amount.get("value") != FIXED_PRICE_USD:
        raise CheckoutError(400, "ORDER_ITEM_AMOUNT_MISMATCH", "The order line item does not match the configured price.")


def capture_order(order_id: str, case: dict[str, str], api_call: Callable[..., dict[str, Any]] | None = None) -> dict[str, Any]:
    if not ORDER_RE.fullmatch(order_id):
        raise CheckoutError(400, "INVALID_ORDER_ID", "Invalid PayPal order ID.")
    call = api_call or paypal_api_request
    order = call("GET", f"/v2/checkout/orders/{order_id}")
    validate_order(order, case, order_id)

    if order.get("status") == "COMPLETED":
        completed = _completed_capture(order)
        if completed is None:
            raise CheckoutError(409, "ORDER_CAPTURE_NOT_COMPLETED", "PayPal marks the order completed but no completed capture is present.")
        capture_id, capture = completed
    elif order.get("status") == "APPROVED":
        captured_order = call("POST", f"/v2/checkout/orders/{order_id}/capture", {})
        if captured_order.get("status") != "COMPLETED":
            raise CheckoutError(402, "PAYMENT_NOT_COMPLETED", "PayPal has not confirmed a completed payment; no report is released.")
        validate_order(captured_order, case, order_id)
        completed = _completed_capture(captured_order)
        if completed is None:
            raise CheckoutError(402, "CAPTURE_NOT_COMPLETED", "PayPal has not confirmed a completed capture; no report is released.")
        capture_id, capture = completed
    else:
        raise CheckoutError(402, "PAYMENT_NOT_APPROVED", "The PayPal order is not approved or completed; no report is released.")

    cap_amount = capture.get("amount")
    if not isinstance(cap_amount, dict) or cap_amount.get("currency_code") != "USD" or cap_amount.get("value") != FIXED_PRICE_USD:
        raise CheckoutError(402, "CAPTURE_AMOUNT_MISMATCH", "The completed capture does not match the fixed product price; no report is released.")
    return {"order_id": order_id, "capture_id": capture_id, "payment_status": "COMPLETED", "case": case}


def refund_capture(capture_id: str, reason: str, api_call: Callable[..., dict[str, Any]] | None = None) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Z0-9-]{5,64}", capture_id):
        raise CheckoutError(500, "CAPTURE_ID_INVALID", "Cannot safely identify the payment capture to refund.")
    call = api_call or paypal_api_request
    try:
        response = call("POST", f"/v2/payments/captures/{capture_id}/refund", {"note_to_payer": reason[:255]})
    except CheckoutError:
        raise
    status = response.get("status")
    if status not in {"COMPLETED", "PENDING"}:
        raise CheckoutError(502, "REFUND_STATUS_UNCONFIRMED", "PayPal did not confirm a completed or pending refund.")
    return {"refund_id": response.get("id"), "refund_status": status}
