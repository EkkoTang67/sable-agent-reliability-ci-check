"""Create an unapproved PayPal Orders v2 order for one fixed-price report."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from http.server import BaseHTTPRequestHandler
from api.common import json_response, method_not_allowed, origin_is_allowed, read_json, public_checkout_config
from lib.paypal import CheckoutError, canonical_case, create_order


def _validated_callback_url(value: object, *, origin: str | None, flag: str) -> str:
    """Accept only an HTTPS return/cancel URL on this exact approved preview origin."""
    from urllib.parse import parse_qs, urlsplit
    if not isinstance(value, str) or not value or len(value) > 4096 or not origin:
        raise CheckoutError(400, "INVALID_RETURN_URL", "A valid same-origin PayPal return/cancel URL is required.")
    parsed = urlsplit(value)
    candidate_origin = f"{parsed.scheme}://{parsed.netloc}"
    query = parse_qs(parsed.query, keep_blank_values=True)
    if (
        parsed.scheme != "https"
        or candidate_origin != origin
        or parsed.path != "/x402-report.html"
        or parsed.username
        or parsed.password
        or query.get(flag) != ["1"]
    ):
        raise CheckoutError(400, "INVALID_RETURN_URL", "PayPal return/cancel URL must point to this HTTPS checkout page.")
    return value


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        allowed, origin = origin_is_allowed(self)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This checkout origin is not approved."}, origin)
            return
        try:
            config = public_checkout_config()
            if not config.get("enabled"):
                json_response(self, 503, {"error": "CHECKOUT_DISABLED", "message": "Checkout is not configured or has not passed its required approval gates.", "reason": config.get("reason")}, origin)
                return
            payload = read_json(self)
            case = canonical_case(payload)
            if "return_url" in payload or "cancel_url" in payload:
                return_url = _validated_callback_url(payload.get("return_url"), origin=origin, flag="paypal_return")
                cancel_url = _validated_callback_url(payload.get("cancel_url"), origin=origin, flag="paypal_cancelled")
                order = create_order(case, return_url=return_url, cancel_url=cancel_url)
            else:
                order = create_order(case)
            json_response(self, 200, {"orderID": order["orderID"], "mode": order["mode"], "approvalUrl": order.get("approvalUrl", "")}, origin)
        except CheckoutError as exc:
            json_response(self, exc.status_code, {"error": exc.code, "message": exc.message}, origin)
        except Exception:
            json_response(self, 500, {"error": "INTERNAL_ERROR", "message": "Could not create the checkout order. No report was generated."}, origin)

    def do_GET(self):
        method_not_allowed(self, "POST")

    def log_message(self, format, *args):
        return
