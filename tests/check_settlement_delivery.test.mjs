import test from "node:test";
import assert from "node:assert/strict";
import { assess } from "../scripts/check_settlement_delivery.mjs";

const base = {
  observations: {
    settlement: { status: "success", source: "fixture", authoritative: true, reference: "capture-1" },
    delivery: { http_status: 402, source: "fixture", authoritative: true, receipt_header_present: false },
  },
};

test("settled but delivery unconfirmed is not reported as full success", () => {
  assert.equal(assess(base).verdict, "SETTLEMENT_CONFIRMED_DELIVERY_UNCONFIRMED");
});

test("requires an authoritative settlement reference", () => {
  const record = structuredClone(base);
  record.observations.settlement.reference = "";
  assert.equal(assess(record).verdict, "UNKNOWN");
});

test("successful delivery requires 2xx and receipt evidence", () => {
  const record = structuredClone(base);
  record.observations.delivery.http_status = 200;
  record.observations.delivery.receipt_header_present = true;
  assert.equal(assess(record).verdict, "SETTLEMENT_AND_DELIVERY_CONFIRMED");
});

test("conflicting failed settlement and successful delivery are escalated", () => {
  const record = structuredClone(base);
  record.observations.settlement.status = "failed";
  record.observations.delivery.http_status = 200;
  assert.equal(assess(record).verdict, "CONFLICT");
});

test("missing observations remain unknown", () => {
  assert.equal(assess({ observations: {} }).verdict, "UNKNOWN");
});
