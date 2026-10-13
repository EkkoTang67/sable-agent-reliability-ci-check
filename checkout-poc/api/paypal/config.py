"""Return only the public PayPal SDK configuration. Never return API secrets."""
from api.common import json_response, method_not_allowed, origin_is_allowed, public_checkout_config

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This checkout origin is not approved."}, origin)
            return
        config = public_checkout_config()
        json_response(self, 200, config, origin)

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        # Keep customer input and transaction hashes out of default request logs.
        return
