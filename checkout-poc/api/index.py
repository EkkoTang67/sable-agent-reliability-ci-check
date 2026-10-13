"""Single Python runtime entry point dispatching the checkout API routes."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit

from api.paypal import config as config_route
from api.paypal import create_order as create_order_route
from api.paypal import capture_order as capture_order_route
from api import demo_report as demo_report_route
from api import receipt_verifier_self_test as receipt_verifier_self_test_route


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/paypal/config":
            return config_route.handler.do_GET(self)
        if path == "/api/paypal/create_order":
            return create_order_route.handler.do_GET(self)
        if path == "/api/paypal/capture_order":
            return capture_order_route.handler.do_GET(self)
        if path == "/api/demo_report":
            return demo_report_route.handler.do_GET(self)
        if path == "/api/receipt_verifier_self_test":
            return receipt_verifier_self_test_route.handler.do_GET(self)
        if path in {"/api", "/api/"}:
            body = b'{"service":"SABLE x402 checkout preview","status":"route-dispatch-ready"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/paypal/config":
            return config_route.handler.do_POST(self)
        if path == "/api/paypal/create_order":
            return create_order_route.handler.do_POST(self)
        if path == "/api/paypal/capture_order":
            return capture_order_route.handler.do_POST(self)
        if path == "/api/demo_report":
            return demo_report_route.handler.do_POST(self)
        if path == "/api/receipt_verifier_self_test":
            return receipt_verifier_self_test_route.handler.do_POST(self)
        self.send_error(404)

    def log_message(self, format, *args):
        return
