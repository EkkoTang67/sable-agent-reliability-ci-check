import test from "node:test";
import assert from "node:assert/strict";

import {
  PRODUCTS,
  getPayPalBaseUrl,
  getPublicCheckoutConfig,
  makeCaptureToken,
  productForSku,
  safeOrderId,
  validatePayPalOrder,
  verifyCaptureToken,
} from "../lib/paypal_checkout.mjs";
import { captureApprovedOrder, verifyPayPalWebhook } from "../lib/paypal_payment_flow.mjs";

const ORDER_ID = "5O190127TN364715T";
const MERCHANT_ID = "SABLEMERCHANT123";
const SKU = "decision-rescue-99";
const SECRET = "test-client-secret-never-used-in-production";

function env(overrides = {}) {
  return {
    PAYPAL_ENV: "sandbox",
    PAYPAL_CLIENT_ID: "test-client-id",
    PAYPAL_CLIENT_SECRET: SECRET,
    PAYPAL_WEBHOOK_ID: "test-webhook-id",
    PAYPAL_MERCHANT_ID: MERCHANT_ID,
    VERCEL_ENV: "preview",
    ...overrides,
  };
}

function makeOrder({ status = "APPROVED", sku = SKU, amount = "99.00", merchantId = MERCHANT_ID, captures = [] } = {}) {
  return {
    id: ORDER_ID,
    status,
    purchase_units: [{
      reference_id: sku,
      custom_id: sku,
      invoice_id: "SABLE-" + sku + "-0123456789ABCDEF",
      amount: { currency_code: "USD", value: amount },
      payee: { merchant_id: merchantId },
      ...(status === "COMPLETED" ? {
        payments: {
          captures: captures.length ? captures : [{
            id: "7AB123456C789012D",
            status: "COMPLETED",
            amount: { currency_code: "USD", value: amount },
            update_time: "2026-10-11T12:00:00Z",
          }],
        },
      } : {}),
    }],
  };
}

function response(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("only the two fixed USD offers are sellable", () => {
  assert.equal(productForSku("decision-rescue-99").amount, "99.00");
  assert.equal(productForSku("decision-closure-299").amount, "299.00");
  assert.equal(productForSku("custom-price-1"), null);
  assert.equal(PRODUCTS["decision-rescue-99"].amountCents, 9900);
  assert.equal(PRODUCTS["decision-closure-299"].amountCents, 29900);
});

test("checkout is disabled until credentials, merchant, webhook and environment all match", () => {
  assert.equal(getPublicCheckoutConfig({}).checkoutEnabled, false);
  assert.equal(getPublicCheckoutConfig(env({ PAYPAL_WEBHOOK_ID: "" })).checkoutEnabled, false);
  assert.equal(getPublicCheckoutConfig(env({ PAYPAL_MERCHANT_ID: "" })).checkoutEnabled, false);
  assert.equal(getPublicCheckoutConfig(env({ PAYPAL_CLIENT_SECRET: "" })).checkoutEnabled, false);
  assert.equal(getPublicCheckoutConfig(env({ VERCEL_ENV: "production" })).checkoutEnabled, false);
  assert.equal(getPublicCheckoutConfig(env({ VERCEL_ENV: "preview", PAYPAL_ENV: "live" })).checkoutEnabled, false);
  assert.equal(getPublicCheckoutConfig(env({ VERCEL_ENV: "production", PAYPAL_ENV: "live" })).checkoutEnabled, true);
  const config = getPublicCheckoutConfig(env());
  assert.equal(config.checkoutEnabled, true);
  assert.equal(config.clientId, "test-client-id");
  assert.equal("clientSecret" in config, false);
  assert.equal(JSON.stringify(config).includes(SECRET), false);
  assert.equal(getPayPalBaseUrl(env()), "https://api-m.sandbox.paypal.com");
  assert.equal(getPayPalBaseUrl(env({ PAYPAL_ENV: "live" })), "https://api-m.paypal.com");
});

test("approved order must match SKU, invoice, amount, currency, and merchant", () => {
  const result = validatePayPalOrder(makeOrder(), SKU, { requireCompleted: false, expectedMerchantId: MERCHANT_ID });
  assert.equal(result.ok, true);
  assert.equal(result.receipt, null, "approval alone never creates a paid receipt");
  assert.ok(validatePayPalOrder(makeOrder({ amount: "1.00" }), SKU, { requireCompleted: false, expectedMerchantId: MERCHANT_ID }).reasons.includes("order_amount_mismatch"));
  assert.ok(validatePayPalOrder(makeOrder({ sku: "decision-closure-299" }), SKU, { requireCompleted: false, expectedMerchantId: MERCHANT_ID }).reasons.includes("product_binding_mismatch"));
  assert.ok(validatePayPalOrder(makeOrder({ merchantId: "SOMEONEELSE" }), SKU, { requireCompleted: false, expectedMerchantId: MERCHANT_ID }).reasons.includes("payee_merchant_mismatch"));
});

test("only one matching completed capture can produce a receipt", () => {
  const valid = validatePayPalOrder(makeOrder({ status: "COMPLETED" }), SKU, { expectedMerchantId: MERCHANT_ID });
  assert.equal(valid.ok, true);
  assert.equal(valid.receipt.verified, true);
  assert.equal(valid.receipt.captureId, "7AB123456C789012D");
  assert.equal(validatePayPalOrder(makeOrder(), SKU, { expectedMerchantId: MERCHANT_ID }).ok, false);
  const twoCaptures = [
    { id: "7AB123456C789012D", status: "COMPLETED", amount: { currency_code: "USD", value: "99.00" } },
    { id: "8BC234567D890123E", status: "COMPLETED", amount: { currency_code: "USD", value: "99.00" } },
  ];
  assert.ok(validatePayPalOrder(makeOrder({ status: "COMPLETED", captures: twoCaptures }), SKU, { expectedMerchantId: MERCHANT_ID }).reasons.includes("multiple_completed_captures"));
  assert.equal(validatePayPalOrder(makeOrder({ status: "COMPLETED", amount: "98.99" }), SKU, { expectedMerchantId: MERCHANT_ID }).ok, false);
});

test("capture token is signed, order- and SKU-bound, and expires", () => {
  const now = Date.parse("2026-10-11T12:00:00Z");
  const token = makeCaptureToken(ORDER_ID, SKU, SECRET, now);
  assert.equal(verifyCaptureToken(token, ORDER_ID, SKU, SECRET, now + 1000), true);
  assert.equal(verifyCaptureToken(token, "ANOTHERORDERID12", SKU, SECRET, now + 1000), false);
  assert.equal(verifyCaptureToken(token, ORDER_ID, "decision-closure-299", SECRET, now + 1000), false);
  assert.equal(verifyCaptureToken(token, ORDER_ID, SKU, "different-secret", now + 1000), false);
  assert.equal(verifyCaptureToken(token, ORDER_ID, SKU, SECRET, now + 91 * 60 * 1000), false);
  assert.equal(verifyCaptureToken("not.a.valid.token", ORDER_ID, SKU, SECRET, now), false);
});

test("PayPal order IDs are constrained before provider paths are constructed", () => {
  assert.equal(safeOrderId(ORDER_ID), true);
  assert.equal(safeOrderId("../sensitive"), false);
  assert.equal(safeOrderId("short"), false);
  assert.equal(safeOrderId(null), false);
});

test("capture reads approval, sends a stable idempotency key, then verifies completed capture", async () => {
  const calls = [];
  const approved = makeOrder();
  const completed = makeOrder({ status: "COMPLETED" });
  const fetchImpl = async (url, options = {}) => {
    const parsed = new URL(url);
    calls.push({ url: parsed.toString(), method: options.method || "GET", headers: options.headers || {} });
    if (parsed.pathname === "/v1/oauth2/token") return response({ access_token: "test-access-token" });
    if (parsed.pathname === "/v2/checkout/orders/" + ORDER_ID && (options.method || "GET") === "GET") return response(approved);
    if (parsed.pathname === "/v2/checkout/orders/" + ORDER_ID + "/capture" && options.method === "POST") return response(completed);
    throw new Error("unexpected_test_fetch:" + parsed.pathname);
  };
  const receipt = await captureApprovedOrder(ORDER_ID, SKU, env(), fetchImpl);
  assert.equal(receipt.orderId, ORDER_ID);
  assert.equal(receipt.captureId, "7AB123456C789012D");
  assert.equal(receipt.verified, true);
  assert.equal(receipt.idempotent, false);
  const captureCall = calls.find(c => c.url.endsWith("/capture"));
  assert.ok(captureCall);
  assert.equal(captureCall.headers["PayPal-Request-Id"], "SABLE-CAPTURE-" + ORDER_ID);
});

test("already-completed order is verified idempotently without capturing again", async () => {
  const calls = [];
  const completed = makeOrder({ status: "COMPLETED" });
  const fetchImpl = async (url, options = {}) => {
    const parsed = new URL(url);
    calls.push({ url: parsed.toString(), method: options.method || "GET" });
    if (parsed.pathname === "/v1/oauth2/token") return response({ access_token: "test-access-token" });
    if (parsed.pathname === "/v2/checkout/orders/" + ORDER_ID) return response(completed);
    throw new Error("unexpected_test_fetch:" + parsed.pathname);
  };
  const receipt = await captureApprovedOrder(ORDER_ID, SKU, env(), fetchImpl);
  assert.equal(receipt.idempotent, true);
  assert.equal(receipt.verified, true);
  assert.equal(calls.some(c => c.url.endsWith("/capture")), false);
});

test("PayPal webhook verification delegates the exact event and registered webhook ID to PayPal", async () => {
  let verificationRequest;
  const event = { id: "WH-TEST-EVENT", event_type: "CHECKOUT.ORDER.APPROVED", resource: { id: ORDER_ID } };
  const headers = {
    "paypal-auth-algo": "SHA256withRSA",
    "paypal-cert-url": "https://api.paypal.com/cert",
    "paypal-transmission-id": "test-transmission",
    "paypal-transmission-sig": "test-signature",
    "paypal-transmission-time": "2026-10-11T12:00:00Z",
  };
  const fetchImpl = async (url, options = {}) => {
    const parsed = new URL(url);
    if (parsed.pathname === "/v1/oauth2/token") return response({ access_token: "test-access-token" });
    if (parsed.pathname === "/v1/notifications/verify-webhook-signature") {
      verificationRequest = JSON.parse(options.body);
      return response({ verification_status: "SUCCESS" });
    }
    throw new Error("unexpected_test_fetch:" + parsed.pathname);
  };
  assert.equal(await verifyPayPalWebhook(event, headers, env(), fetchImpl), true);
  assert.equal(verificationRequest.webhook_id, "test-webhook-id");
  assert.equal(verificationRequest.webhook_event.id, event.id);
  assert.equal(verificationRequest.transmission_sig, headers["paypal-transmission-sig"]);
  assert.equal(await verifyPayPalWebhook(event, {}, env(), fetchImpl).catch(() => false), false);
});
