# Example — US$99 Micro Closure Receipt

> **SYNTHETIC EXAMPLE ONLY.** No real customer, payment provider, account, production system, or commercial result is represented here.

This human-readable example mirrors the proposed structure in [`outcome-proof-receipt-v1.synthetic.json`](outcome-proof-receipt-v1.synthetic.json). It shows the shape of a deliverable—not a claim that the current CLI has produced a provider-authenticated customer receipt.

## Receipt summary

| Field | Example value |
|---|---|
| Receipt ID | `synthetic-payment-access-001` |
| Claim | One settled test payment grants the intended account the matching paid entitlement |
| Boundary | Synthetic checkout + account-service fixture |
| Environment | Test fixture; read-only observation |
| Revision | `fixture-v1` |
| Correlation | `purchase-chain-hash-demo-001` |
| Verdict | **VERIFIED — in this synthetic fixture only** |

## What was observed

| Source (synthetic) | Observation | Reference |
|---|---|---|
| Payment ledger | Payment is `settled` | `pay_test_demo_001` |
| Entitlement store | Entitlement is `active` and references the same payment ID | `entitlement_demo_001` |

## Checks

1. **Payment settled:** the fixture records the payment as settled.
2. **Outcome bound to the same payment:** the active entitlement references `pay_test_demo_001`, the same identity as the settled payment.

Both checks are marked `VERIFIED` only because the synthetic fixture contains both corresponding observations. A successful checkout response alone would not prove entitlement.

## Required limitations in a real receipt

A real engagement must state the exact candidate revision, authorized boundary, observation sources, timestamps, evidence references, checks, verdict, and anything that could not be independently established. If source authority, freshness, correlation, or access is insufficient, the result remains `UNKNOWN` or records an `EVIDENCE GAP`; SABLE must not fill missing evidence with assumptions.

## What this example does **not** prove

- It is not a real payment, customer outcome, provider response, or production test.
- The source names and observations are fixture-defined, not provider-authenticated.
- It does not establish production readiness, universal exactly-once behavior, or certification.
- It does not prove that every current SABLE command emits this exact receipt contract. The relevant command or adapter must be tested for the engagement before making that claim.

The paid unit is the **authorized bounded verification and its evidence**, not a guaranteed positive verdict. Testing starts only after the claim, scope, authority, and execution boundary are agreed.
