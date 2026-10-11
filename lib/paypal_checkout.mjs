import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";

export const PRODUCTS = Object.freeze({
  "decision-rescue-99": Object.freeze({
    sku: "decision-rescue-99",
    title: "SABLE One-Claim Outcome Check",
    description: "One bounded, authorized outcome-verification check and evidence receipt.",
    amount: "99.00",
    amountCents: 9900,
    currency: "USD",
    paypalMeUrl: "https://paypal.me/tang665/99USD",
  }),
  "decision-closure-299": Object.freeze({
    sku: "decision-closure-299",
    title: "SABLE Decision Closure",
    description: "A broader bounded verification across replay, multi-state, or provenance boundaries.",
    amount: "299.00",
    amountCents: 29900,
    currency: "USD",
    paypalMeUrl: "https://paypal.me/tang665/299USD",
  }),
});

export function productForSku(sku) {
  return typeof sku === "string" && Object.hasOwn(PRODUCTS, sku) ? PRODUCTS[sku] : null;
}

export function getPayPalMode(env = process.env) {
  return String(env.PAYPAL_ENV || "sandbox").trim().toLowerCase() === "live" ? "live" : "sandbox";
}

export function getPayPalBaseUrl(env = process.env) {
  return getPayPalMode(env) === "live"
    ? "https://api-m.paypal.com"
    : "https://api-m.sandbox.paypal.com";
}

export function getPublicCheckoutConfig(env = process.env) {
  const mode = getPayPalMode(env);
  const credentialsPresent = Boolean(
    String(env.PAYPAL_CLIENT_ID || "").trim() &&
    String(env.PAYPAL_CLIENT_SECRET || "").trim()
  );
  // Never accidentally expose a sandbox checkout as a live production purchase.
  const environmentMatches = env.VERCEL_ENV === "production" ? mode === "live" : mode === "sandbox";
  const webhookConfigured = Boolean(String(env.PAYPAL_WEBHOOK_ID || "").trim());
  const merchantConfigured = Boolean(String(env.PAYPAL_MERCHANT_ID || "").trim());
  // Live checkout stays disabled until the signed webhook route and destination merchant are configured.
  const checkoutEnabled = credentialsPresent && webhookConfigured && merchantConfigured && environmentMatches;
  return {
    checkoutEnabled,
    mode,
    clientId: checkoutEnabled ? String(env.PAYPAL_CLIENT_ID).trim() : null,
    webhookConfigured,
    merchantConfigured,
    products: Object.values(PRODUCTS).map(({ sku, title, description, amount, currency, paypalMeUrl }) => ({
      sku,
      title,
      description,
      amount,
      currency,
      paypalMeUrl,
    })),
  };
}

export function moneyMatches(amount, product) {
  if (!amount || amount.currency_code !== product.currency) return false;
  const value = Number(amount.value);
  return Number.isFinite(value) && Math.round(value * 100) === product.amountCents;
}

export function validatePayPalOrder(order, sku, { requireCompleted = true, expectedMerchantId } = {}) {
  const reasons = [];
  const product = productForSku(sku);
  if (!product) return { ok: false, reasons: ["unknown_product"], receipt: null };
  if (!order || typeof order !== "object") {
    return { ok: false, reasons: ["order_missing"], receipt: null };
  }

  if (requireCompleted) {
    if (order.status !== "COMPLETED") reasons.push("order_not_completed");
  } else if (order.status !== "APPROVED") {
    reasons.push("order_not_approved");
  }

  if (!Array.isArray(order.purchase_units) || order.purchase_units.length !== 1) {
    reasons.push("purchase_unit_count_mismatch");
  }

  const unit = Array.isArray(order.purchase_units) && order.purchase_units.length === 1
    ? order.purchase_units[0]
    : null;

  if (unit) {
    if (expectedMerchantId) {
      const actualMerchantId = String(unit.payee?.merchant_id || "");
      if (!actualMerchantId || actualMerchantId !== expectedMerchantId) reasons.push("payee_merchant_mismatch");
    }
    if (unit.custom_id !== product.sku || unit.reference_id !== product.sku) {
      reasons.push("product_binding_mismatch");
    }
    if (!moneyMatches(unit.amount, product)) reasons.push("order_amount_mismatch");
    if (requireCompleted && !String(unit.invoice_id || "").startsWith("SABLE-" + product.sku + "-")) {
      reasons.push("invoice_binding_mismatch");
    }
    if (!requireCompleted && !String(unit.invoice_id || "").startsWith("SABLE-" + product.sku + "-")) {
      reasons.push("invoice_binding_mismatch");
    }
  }

  let completedCaptures = [];
  if (requireCompleted) {
    completedCaptures = unit?.payments?.captures?.filter((capture) => capture?.status === "COMPLETED") || [];
    if (completedCaptures.length !== 1) {
      reasons.push(completedCaptures.length > 1 ? "multiple_completed_captures" : "completed_capture_missing");
    } else if (!moneyMatches(completedCaptures[0].amount, product)) {
      reasons.push("capture_amount_mismatch");
    } else if (!String(completedCaptures[0].id || "").trim()) {
      reasons.push("capture_id_missing");
    }
  }

  const ok = reasons.length === 0;
  const capture = completedCaptures[0] || null;
  return {
    ok,
    reasons,
    // Never emit a payment receipt for an approved-but-not-completed order.
    receipt: ok && requireCompleted ? {
      orderId: order.id,
      captureId: capture?.id || null,
      sku: product.sku,
      amount: product.amount,
      currency: product.currency,
      paidAt: capture?.update_time || capture?.create_time || order.update_time || null,
      verified: true,
    } : null,
  };
}

export function makeCaptureToken(orderId, sku, secret, now = Date.now()) {
  if (!orderId || !productForSku(sku) || !secret) throw new Error("capture_token_inputs_invalid");
  const payload = Buffer.from(JSON.stringify({
    orderId,
    sku,
    issuedAt: now,
    nonce: randomUUID(),
  })).toString("base64url");
  const signature = createHmac("sha256", secret).update(payload).digest("base64url");
  return `${payload}.${signature}`;
}

export function verifyCaptureToken(token, expectedOrderId, expectedSku, secret, now = Date.now()) {
  if (typeof token !== "string" || !secret) return false;
  const parts = token.split(".");
  if (parts.length !== 2) return false;
  const [payload, providedSignature] = parts;
  let provided;
  try {
    provided = Buffer.from(providedSignature, "base64url");
  } catch {
    return false;
  }
  const expected = createHmac("sha256", secret).update(payload).digest();
  if (provided.length !== expected.length || !timingSafeEqual(provided, expected)) return false;

  let decoded;
  try {
    decoded = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
  } catch {
    return false;
  }
  const issuedAt = Number(decoded?.issuedAt);
  const ttlMs = 90 * 60 * 1000;
  return decoded?.orderId === expectedOrderId
    && decoded?.sku === expectedSku
    && Number.isFinite(issuedAt)
    && issuedAt <= now + 60_000
    && now - issuedAt <= ttlMs;
}

export function safeOrderId(value) {
  return typeof value === "string" && /^[A-Z0-9]{10,40}$/.test(value);
}

export function parseRequestBody(body) {
  if (body && typeof body === "object" && !Array.isArray(body)) return body;
  if (typeof body === "string") {
    try {
      const parsed = JSON.parse(body);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }
  return null;
}

function parseJson(text) {
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return {};
  }
}

export async function getPayPalAccessToken(env = process.env, fetchImpl = fetch) {
  const clientId = String(env.PAYPAL_CLIENT_ID || "").trim();
  const clientSecret = String(env.PAYPAL_CLIENT_SECRET || "").trim();
  if (!clientId || !clientSecret) throw new Error("paypal_credentials_not_configured");

  const response = await fetchImpl(`${getPayPalBaseUrl(env)}/v1/oauth2/token`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString("base64")}`,
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body: "grant_type=client_credentials",
  });
  const text = await response.text();
  const data = parseJson(text);
  if (!response.ok || !data.access_token) {
    const error = new Error("paypal_oauth_failed");
    error.status = response.status;
    throw error;
  }
  return data.access_token;
}

export async function paypalApiRequest(path, {
  method = "GET",
  body,
  requestId,
  env = process.env,
  fetchImpl = fetch,
} = {}) {
  const token = await getPayPalAccessToken(env, fetchImpl);
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (requestId) headers["PayPal-Request-Id"] = requestId;

  const response = await fetchImpl(`${getPayPalBaseUrl(env)}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  const data = parseJson(text);
  if (!response.ok) {
    const error = new Error("paypal_api_request_failed");
    error.status = response.status;
    error.providerName = String(data.name || "unknown");
    throw error;
  }
  return data;
}

export function makeInvoiceId(sku) {
  if (!productForSku(sku)) throw new Error("unknown_product");
  return `SABLE-${sku}-${randomUUID().replaceAll("-", "").slice(0, 16)}`;
}
