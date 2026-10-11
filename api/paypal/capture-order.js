import {
  getPublicCheckoutConfig,
  parseRequestBody,
  productForSku,
  safeOrderId,
  verifyCaptureToken,
} from "../../lib/paypal_checkout.mjs";
import { captureApprovedOrder } from "../../lib/paypal_payment_flow.mjs";
import { applyPublicCors, safeErrorStatus, sendMethodNotAllowed } from "../../lib/http.mjs";

export default async function handler(req, res) {
  if (!applyPublicCors(req, res, ["POST"])) return;
  if (req.method !== "POST") return sendMethodNotAllowed(res, ["POST"]);
  res.setHeader("Cache-Control", "no-store, max-age=0");

  if (!getPublicCheckoutConfig().checkoutEnabled) {
    return res.status(503).json({ error: "paypal_checkout_not_configured", directPaymentAvailable: true });
  }
  const body = parseRequestBody(req.body);
  const orderID = body?.orderID;
  const sku = body?.sku;
  const captureToken = body?.captureToken;
  if (!safeOrderId(orderID) || !productForSku(sku) || typeof captureToken !== "string") {
    return res.status(400).json({ error: "capture_request_invalid" });
  }
  if (!verifyCaptureToken(captureToken, orderID, sku, process.env.PAYPAL_CLIENT_SECRET)) {
    return res.status(401).json({ error: "capture_token_invalid_or_expired" });
  }

  try {
    const receipt = await captureApprovedOrder(orderID, sku);
    return res.status(200).json({
      paymentVerified: true,
      verdict: "PAYMENT_VERIFIED",
      receipt,
      intake: {
        required: true,
        message: "Payment is verified. Send the bounded claim and authorized scope using the scope email action shown on the receipt page.",
      },
    });
  } catch (error) {
    console.error("[paypal.capture-order]", error?.providerName || error?.message || "unknown_error");
    const message = String(error?.message || "");
    if (message.startsWith("paypal_approval_rejected:") || message.startsWith("paypal_completed_order_rejected:")) {
      return res.status(422).json({ error: "paypal_order_does_not_match_fixed_offer" });
    }
    if (message === "paypal_checkout_not_configured") {
      return res.status(503).json({ error: "paypal_checkout_not_configured" });
    }
    return res.status(safeErrorStatus(error)).json({
      error: "payment_not_yet_verified",
      message: "PayPal has not returned independently verifiable completed-capture evidence. Do not retry a live payment unless the order status is checked again.",
    });
  }
}
