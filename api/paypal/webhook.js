import { getPublicCheckoutConfig, parseRequestBody, safeOrderId } from "../../lib/paypal_checkout.mjs";
import { captureApprovedOrder, getOrder, validateOrder, verifyPayPalWebhook } from "../../lib/paypal_payment_flow.mjs";
import { applyPublicCors, sendMethodNotAllowed } from "../../lib/http.mjs";

export default async function handler(req, res) {
  if (!applyPublicCors(req, res, ["POST"])) return;
  if (req.method !== "POST") return sendMethodNotAllowed(res, ["POST"]);
  res.setHeader("Cache-Control", "no-store, max-age=0");

  if (!getPublicCheckoutConfig().webhookConfigured) {
    return res.status(503).json({ error: "paypal_webhook_not_configured" });
  }
  const event = parseRequestBody(req.body);
  if (!event || typeof event.event_type !== "string" || !event.id) {
    return res.status(400).json({ error: "invalid_webhook_event" });
  }

  try {
    const verifiedSignature = await verifyPayPalWebhook(event, req.headers || {});
    if (!verifiedSignature) return res.status(401).json({ error: "webhook_signature_invalid" });

    if (event.event_type === "CHECKOUT.ORDER.APPROVED") {
      const orderID = event.resource?.id;
      if (!safeOrderId(orderID)) return res.status(400).json({ error: "approved_order_id_missing" });
      // Capture is idempotent at PayPal and uses a stable request ID, so a browser callback
      // racing this webhook cannot create a second capture for the same order.
      const order = await getOrder(orderID);
      const sku = order?.purchase_units?.length === 1 ? order.purchase_units[0]?.custom_id : null;
      const approval = validateOrder(order, sku, process.env, false);
      if (!approval.ok) return res.status(422).json({ error: "approved_order_not_eligible_for_capture" });
      const receipt = await captureApprovedOrder(orderID, sku);
      return res.status(200).json({ received: true, captured: true, paymentVerified: true, receipt });
    }

    if (event.event_type === "PAYMENT.CAPTURE.COMPLETED") {
      // Signature-verified acknowledgement only. Fulfilment still requires a completed,
      // merchant-matched order read through capture-order or the approved-order handler.
      return res.status(200).json({ received: true, verifiedSignature: true });
    }

    if ([
      "PAYMENT.CAPTURE.DENIED",
      "CHECKOUT.ORDER.VOIDED",
      "CHECKOUT.PAYMENT-APPROVAL.REVERSED",
    ].includes(event.event_type)) {
      return res.status(200).json({ received: true, noFulfilment: true });
    }

    return res.status(200).json({ received: true, ignored: true });
  } catch (error) {
    console.error("[paypal.webhook]", error?.providerName || error?.message || "unknown_error");
    return res.status(500).json({ error: "webhook_processing_failed" });
  }
}
