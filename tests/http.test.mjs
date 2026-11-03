import test from "node:test";
import assert from "node:assert/strict";
import { applyPublicCors } from "../lib/http.mjs";

function harness({ origin, method = "POST", env = {} } = {}) {
  const previous = {
    VERCEL_URL: process.env.VERCEL_URL,
    VERCEL_BRANCH_URL: process.env.VERCEL_BRANCH_URL,
    SABLE_ALLOWED_ORIGINS: process.env.SABLE_ALLOWED_ORIGINS,
  };
  for (const key of Object.keys(previous)) {
    if (Object.hasOwn(env, key)) process.env[key] = env[key];
    else delete process.env[key];
  }
  const headers = {};
  let statusCode = 200;
  let body;
  const res = {
    setHeader(key, value) { headers[key] = value; },
    status(code) { statusCode = code; return this; },
    json(value) { body = value; return this; },
    end() { return this; },
  };
  const accepted = applyPublicCors({ method, headers: origin ? { origin } : {} }, res, ["POST"]);
  for (const [key, value] of Object.entries(previous)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  return { accepted, headers, statusCode, body };
}

test("allows the current Vercel immutable deployment origin", () => {
  const result = harness({
    origin: "https://sable-code-to-cash-sandbox-3ics1y6ph-1164752614-9151.vercel.app",
    env: { VERCEL_URL: "sable-code-to-cash-sandbox-3ics1y6ph-1164752614-9151.vercel.app" },
  });
  assert.equal(result.accepted, true);
  assert.equal(result.headers["Access-Control-Allow-Origin"], "https://sable-code-to-cash-sandbox-3ics1y6ph-1164752614-9151.vercel.app");
});

test("allows the stable Vercel branch alias when supplied by Vercel", () => {
  const result = harness({
    origin: "https://sable-code-to-cash-sandbox-git-feat-code-c035fc-1164752614-9151.vercel.app",
    env: { VERCEL_BRANCH_URL: "sable-code-to-cash-sandbox-git-feat-code-c035fc-1164752614-9151.vercel.app" },
  });
  assert.equal(result.accepted, true);
});

test("rejects an unrelated origin", () => {
  const result = harness({
    origin: "https://untrusted.example",
    env: { VERCEL_URL: "sable-code-to-cash-sandbox-3ics1y6ph-1164752614-9151.vercel.app" },
  });
  assert.equal(result.accepted, false);
  assert.equal(result.statusCode, 403);
  assert.deepEqual(result.body, { error: "origin_not_allowed" });
});

test("preflight returns 204 for an allowed deployment origin", () => {
  const result = harness({
    origin: "https://sable-code-to-cash-sandbox-3ics1y6ph-1164752614-9151.vercel.app",
    method: "OPTIONS",
    env: { VERCEL_URL: "sable-code-to-cash-sandbox-3ics1y6ph-1164752614-9151.vercel.app" },
  });
  assert.equal(result.accepted, false);
  assert.equal(result.statusCode, 204);
});
