"""Capture a PayPal order, then automatically deliver the public evidence report."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from http.server import BaseHTTPRequestHandler
from api.common import json_response, method_not_allowed, origin_is_allowed, read_json, public_checkout_config
from lib.paypal import CheckoutError, canonical_case, capture_order, refund_capture
from scripts.sable_x402_service import collect_report

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        allowed, origin = origin_is_allowed(self)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This checkout origin is not approved."}, origin)
            return
        payment = None
        try:
            config = public_checkout_config()
            if not config.get("enabled"):
                json_response(self, 503, {"error": "CHECKOUT_DISABLED", "message": "Checkout is not configured or has not passed its required approval gates.", "reason": config.get("reason")}, origin)
                return
            payload = read_json(self)
            order_id = payload.get("orderID")
            if not isinstance(order_id, str):
                raise CheckoutError(400, "INVALID_ORDER_ID", "orderID is required.")
            case = canonical_case(payload.get("case"))
            payment = capture_order(order_id, case)
            report = collect_report(case)
            collector = report.get("collector") if isinstance(report, dict) else None
            fetched_sources = collector.get("fetched_sources", []) if isinstance(collector, dict) else []
            if not fetched_sources:
                try:
                    refund = refund_capture(payment["capture_id"], "SABLE report could not reach any public evidence source; automatic refund.")
                    json_response(self, 503, {"error": "PUBLIC_EVIDENCE_SOURCES_UNAVAILABLE", "message": "No public evidence source could be reached. The report was not delivered; PayPal refund status is shown below.", "orderID": order_id, "payment_status": payment["payment_status"], "refund_status": refund["refund_status"], "refund_id": refund.get("refund_id")}, origin)
                except Exception:
                    json_response(self, 502, {"error": "REFUND_NOT_CONFIRMED", "message": "Payment was captured, but public sources and the automatic refund could not be confirmed. Do not pay again. Contact support with the order reference.", "orderID": order_id, "capture_id": payment["capture_id"], "payment_status": payment["payment_status"]}, origin)
                return
            response = {"product": "SABLE x402 public evidence report", "payment_status": payment["payment_status"], "payment_reference": {"order_id": payment["order_id"], "capture_id": payment["capture_id"]}, "report": report, "delivery_note": "This is a public-evidence report. UNKNOWN is a valid result; payment does not buy a positive verdict."}
            json_response(self, 200, response, origin)
        except CheckoutError as exc:
            json_response(self, exc.status_code, {"error": exc.code, "message": exc.message, "report_delivered": False}, origin)
        except Exception:
            if payment and payment.get("capture_id"):
                try:
                    refund = refund_capture(payment["capture_id"], "SABLE could not generate or deliver the purchased report; automatic refund attempt.")
                    refund_result = {"refund_status": refund["refund_status"], "refund_id": refund.get("refund_id")}
                    msg = "Report generation failed. An automatic refund has been submitted; use the order reference if support is needed."
                    status = 502
                except Exception:
                    refund_result = {"refund_status": "UNCONFIRMED"}
                    msg = "Payment was captured, but report generation and refund could not be confirmed. Do not pay again; contact support with this order reference."
                    status = 502
                json_response(self, status, {"error": "REPORT_GENERATION_FAILED", "message": msg, "orderID": payment.get("order_id"), "capture_id": payment.get("capture_id"), "payment_status": payment.get("payment_status"), **refund_result}, origin)
            else:
                json_response(self, 500, {"error": "INTERNAL_ERROR", "message": "Capture and report process could not be completed. No report was delivered."}, origin)

    def do_GET(self):
        method_not_allowed(self, "POST")

    def log_message(self, format, *args):
        return
