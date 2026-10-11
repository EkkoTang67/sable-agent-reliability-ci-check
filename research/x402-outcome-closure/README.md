# x402 outcome-closure research spike

## Commercial hypothesis (not validated)
A payment can settle while the buyer receives a failed response or loses the settlement receipt. A narrow tool could replay a captured, redacted trace and answer: **what does the evidence establish about settlement and delivery?**

## Public trigger cases
- x402 issue #3732: a reported Next.js wrapper case where successful settlement is followed by a reconstructed 402 response and a missing settlement header for null-body statuses. The issue describes a local fixture, not proven production loss.
- x402 issue #3730: a reported batch-settlement refund path where claimed funds are not picked up by the settle job in the described reproduction. The report uses Anvil; do not infer production exposure.

## This spike does
- Validate a small, provider-neutral JSON observation record.
- Distinguish evidence states: `SETTLEMENT_CONFIRMED_DELIVERY_UNCONFIRMED`, `SETTLEMENT_AND_DELIVERY_CONFIRMED`, `CONFLICT`, `UNKNOWN`.
- Emit explicit evidence gaps and avoid treating HTTP status alone as authoritative proof of payment.

## This spike does not
- Connect to a facilitator, chain, wallet, provider, or production merchant.
- prove real funds moved; certify x402; issue a refund; or authorize retries.
- establish customer demand, a budget, or a paid order.

## Run
```sh
node --test tests/check_settlement_delivery.test.mjs
node scripts/check_settlement_delivery.mjs examples/settlement-response-mismatch.json
```

## Commercial gate
Do not expand this into a product until a named buyer confirms all of:
1. A current release, settlement, refund, or delivery decision blocked by this evidence gap.
2. The economic consequence and decision deadline.
3. The person with payment authority and a budget/payment path.
4. Why internal logs or an existing dashboard cannot close it.
5. A bounded paid pilot with agreed evidence inputs and acceptance criteria.

Current status: **technical hypothesis only; payer, budget, and settled revenue unconfirmed.**
