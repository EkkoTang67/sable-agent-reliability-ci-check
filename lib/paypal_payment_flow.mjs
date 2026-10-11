import {
  getPublicCheckoutConfig,
  paypalApiRequest,
  safeOrderId,
  validatePayPalOrder,
} from "./paypal_checkout.mjs";

function expectedMerchant(env) {
  return String(env.PAYPAL_MERCHANT_ID || "").trim();
}

export async function getOrder(orderID, env = process.env, fetchImpl = fetch) {
  if (!safeOrderId(orderID)) throw new Error("invalid_order_id");
  return paypalApiRequest(
    `/v2/checkout/orders/${encodeURIComponent(orderID)}`,
    { method: "GET", env, fetchImpl },
  );
}

export function validateOrder(order, sku, env = process.env, requireCompleted = true) {
  const merchantId = expectedMerchant(env);
  if (!merchantId) return { ok: false, reasons: ["merchant_not_configured"], receipt: null };
  return validatePayPalOrder(order, sku, {
    requireCompleted,
    expectedMerchantId: merchantId,
  });
}

export async function captureApprovedOrder(orderID, sku, env = process.env, fetchImpl = fetch) {
  const config = getPublicCheckoutConfig(env);
  if (!config.checkoutEnabled) throw new Error("paypal_checkout_not_configured");
  if (!safeOrderId(orderID)) throw new Error("invalid_order_id");

  let order = await getOrder(orderID, env, fetchImpl);
  if (order.status === "COMPLETED") {
    const existing = validateOrder(order, sku, env, true);
    if (!existing.ok) throw new Error(`paypal_completed_order_rejected:${existing.reasons.join(",")}`);
    return { ...existing.receipt, orderStatus: order.status, idempotent: true };
  }

  const approval = validateOrder(order, sku, env, false);
  if (!approval.ok) throw new Error(`paypal_approval_rejected:${approval.reasons.join(",")}`);

  try {
    order = await paypalApiRequest(
      `/v2/checkout/orders/${encodeURIComponent(orderID)}/capture`,
      {
        method: "POST",
        body: {},
        requestId: `SABLE-CAPTURE-${orderID}`,
        env,
        fetchImpl,
      },
    );
  } catch (captureError) {
    // A client callback and an approved-order webhook can race. Read PayPal's record
    // again before reporting failure; never infer payment from the approval itself.
    order = await getOrder(orderID, env, fetchImpl);
    if (order.status !== "COMPLETED") throw captureError;
  }

  const verified = validateOrder(order, sku, env, true);
  if (!verified.ok) throw new Error(`paypal_capture_not_verified:${verified.reasons.join(",")}`);
  return { ...verified.receipt, orderStatus: order.status, idempotent: false };
}

export async function verifyPayPalWebhook(event, headers, env = process.env, fetchImpl = fetch) {
  const config = getPublicCheckoutConfig(env);
  if (!config.webhookConfigured || !String(env.PAYPAL_WEBHOOK_ID || "").trim()) {
    throw new Error("paypal_webhook_not_configured");
  }
  const requiredHeaders = [
    "paypal-auth-algo",
    "paypal-cert-url",
    "paypal-transmission-id",
    "paypal-transmission-sig",
    "paypal-transmission-time",
  ];
  for (const name of requiredHeaders) {
    if (!String(headers?.[name] || "").trim()) throw new Error("paypal_webhook_headers_missing");
  }

  const result = await paypalApiRequest(
    "/v1/notifications/verify-webhook-signature",
    {
      method: "POST",
      body: {
        auth_algo: headers["paypal-auth-algo"],
        cert_url: headers["paypal-cert-url"],
        transmission_id: headers["paypal-transmission-id"],
        transmission_sig: headers["paypal-transmission-sig"],
        transmission_time: headers["paypal-transmission-time"],
        webhook_id: String(env.PAYPAL_WEBHOOK_ID).trim(),
        webhook_event: event,
      },
      env,
      fetchImpl,
    },
  );
  return result.verification_status === "SUCCESS";
}
