"""Free, read-only sample report for one public Base transaction; no payment flow."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from api.common import allowed_origins, json_response, method_not_allowed, origin_is_allowed
from scripts.sable_x402_collect import BASE_NATIVE_USDC
from scripts.sable_x402_service import collect_report

# Intentionally fixed to a public sample case. This endpoint accepts no user-controlled
# URLs, slugs, transaction hashes, or other inputs, so it cannot be used as an arbitrary fetch proxy.
DEMO_CASE = {
    "transaction_hash": "0x77bd390b27324e279ee1e227ccb58386135a2c68fe135e46c2608f34877b4526",
    "slug": "feeds",
    "expected_amount": "0.05",
    "recipient": "0x367f1b3d8ca90d1e087481a9a40d585bf3451a03",
    "asset": "USDC",
    "asset_contract": BASE_NATIVE_USDC,
    "endpoint": "/feeds/api/query",
    "network": "eip155:8453",
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This demo origin is not approved."}, origin)
            return
        try:
            report = collect_report(DEMO_CASE)
            payload = {
                "product": "SABLE public x402 evidence report — free demo",
                "demo": True,
                "payment_required": False,
                "warning": "This is a fixed public sample case, not a buyer-specific report. UNKNOWN is a valid result and does not mean payment failed.",
                "report": report,
            }
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            # This fixed public case can be briefly cached at the edge; source timestamps stay in the report.
            self.send_header("Cache-Control", "public, s-maxage=60, stale-while-revalidate=300")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if origin and origin in allowed_origins():
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            json_response(self, 502, {"error": "DEMO_REPORT_UNAVAILABLE", "message": "The free read-only sample could not be generated right now. No payment was taken."}, origin)

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        # Do not write transaction payloads or source exceptions into default request logs.
        return
