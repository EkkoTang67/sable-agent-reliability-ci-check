"""Create an unapproved PayPal Orders v2 order for one fixed-price report."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from http.server import BaseHTTPRequestHandler
from api.common import json_response, method_not_allowed, origin_is_allowed, read_json, public_checkout_config
from lib.paypal import CheckoutError, canonical_case, create_order

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
            order = create_order(case)
            json_response(self, 200, {"orderID": order["orderID"], "mode": order["mode"]}, origin)
        except CheckoutError as exc:
            json_response(self, exc.status_code, {"error": exc.code, "message": exc.message}, origin)
        except Exception:
            json_response(self, 500, {"error": "INTERNAL_ERROR", "message": "Could not create the checkout order. No report was generated."}, origin)

    def do_GET(self):
        method_not_allowed(self, "POST")

    def log_message(self, format, *args):
        return
