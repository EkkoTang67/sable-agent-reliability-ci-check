import { randomUUID } from "node:crypto";
import {
  getPublicCheckoutConfig,
  makeInvoiceId,
  makeCaptureToken,
  parseRequestBody,
  paypalApiRequest,
  productForSku,
} from "../../lib/paypal_checkout.mjs";
import { applyPublicCors, safeErrorStatus, sendMethodNotAllowed } from "../../lib/http.mjs";

export default async function handler(req, res) {
  if (!applyPublicCors(req, res, ["POST"])) return;
  if (req.method !== "POST") return sendMethodNotAllowed(res, ["POST"]);
  res.setHeader("Cache-Control", "no-store, max-age=0");

  const config = getPublicCheckoutConfig();
  if (!config.checkoutEnabled) {
    return res.status(503).json({ error: "paypal_checkout_not_configured", directPaymentAvailable: true });
  }

  const body = parseRequestBody(req.body);
  const product = productForSku(body?.sku);
  if (!product) return res.status(400).json({ error: "unknown_product" });

  const invoiceId = makeInvoiceId(product.sku);
  try {
    const order = await paypalApiRequest("/v2/checkout/orders", {
      method: "POST",
      requestId: `SBL-ORD-${randomUUID().replaceAll("-", "").slice(0, 24)}`, 
      body: {
        intent: "CAPTURE",
        purchase_units: [{
          reference_id: product.sku,
          custom_id: product.sku,
          payee: { merchant_id: process.env.PAYPAL_MERCHANT_ID },
          invoice_id: invoiceId,
          description: product.description,
          amount: { currency_code: product.currency, value: product.amount },
        }],
        application_context: {
          brand_name: "SABLE",
          user_action: "PAY_NOW",
          shipping_preference: "NO_SHIPPING",
        },
      },
    });
    if (!order?.id || order.status !== "CREATED") {
      return res.status(502).json({ error: "paypal_order_creation_unconfirmed" });
    }

    // The token binds the approved order ID to the fixed SKU. It is not a PayPal credential.
    const captureToken = makeCaptureToken(order.id, product.sku, process.env.PAYPAL_CLIENT_SECRET);
    return res.status(201).json({
      id: order.id,
      sku: product.sku,
      amount: product.amount,
      currency: product.currency,
      captureToken,
    });
  } catch (error) {
    console.error("[paypal.create-order]", error?.providerName || error?.message || "unknown_error");
    return res.status(safeErrorStatus(error)).json({ error: "paypal_order_creation_failed" });
  }
}
