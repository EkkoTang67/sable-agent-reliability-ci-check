#!/usr/bin/env node
import fs from "node:fs";

const ALLOWED = new Set([
  "SETTLEMENT_AND_DELIVERY_CONFIRMED",
  "SETTLEMENT_CONFIRMED_DELIVERY_UNCONFIRMED",
  "CONFLICT",
  "UNKNOWN",
]);

export function assess(record) {
  const s = record?.observations?.settlement;
  const d = record?.observations?.delivery;
  const gaps = [];
  if (!s || typeof s.status !== "string" || !s.source) gaps.push("missing settlement status or source");
  if (!d || !d.source || !Number.isInteger(d.http_status)) gaps.push("missing delivery status or source");
  if (gaps.length) return { verdict: "UNKNOWN", gaps };

  const settlementConfirmed = s.status === "success" && s.authoritative === true && Boolean(s.reference);
  const deliveryConfirmed = d.authoritative === true && d.http_status >= 200 && d.http_status < 300 && d.receipt_header_present === true;

  if (s.status === "failed" && d.http_status >= 200 && d.http_status < 300) {
    return { verdict: "CONFLICT", gaps: ["delivery appears successful while settlement is reported failed; reconcile against authoritative records"] };
  }
  if (!settlementConfirmed) {
    return { verdict: "UNKNOWN", gaps: ["settlement is not established by an authoritative status and reference"] };
  }
  if (deliveryConfirmed) return { verdict: "SETTLEMENT_AND_DELIVERY_CONFIRMED", gaps: [] };
  return { verdict: "SETTLEMENT_CONFIRMED_DELIVERY_UNCONFIRMED", gaps: ["settlement evidence exists, but the supplied delivery evidence does not establish successful delivery"] };
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const file = process.argv[2];
  if (!file) {
    console.error("Usage: node scripts/check_settlement_delivery.mjs <record.json>");
    process.exitCode = 2;
  } else {
    try {
      const record = JSON.parse(fs.readFileSync(file, "utf8"));
      const result = assess(record);
      if (!ALLOWED.has(result.verdict)) throw new Error("internal verdict error");
      console.log(JSON.stringify({ case_id: record.case_id ?? null, fixture_type: record.fixture_type ?? "unspecified", ...result, production_verified: false }, null, 2));
    } catch (error) {
      console.error(`Unable to assess record: ${error.message}`);
      process.exitCode = 1;
    }
  }
}
