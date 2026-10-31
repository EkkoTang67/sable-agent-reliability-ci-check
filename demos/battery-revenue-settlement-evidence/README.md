# Battery Revenue Settlement Evidence Checker — synthetic MVP

A contract-driven evidence checker for one narrow case: a fixed monthly battery availability payment with a contract-specified availability target and penalty per percentage point below target. It compares the derived contract amount with invoice, settlement and payment records.

## Run
```bash
python3 -m unittest -v
python3 battery_settlement.py sample_batch.json
python3 battery_settlement.py incomplete_batch.json
```

## Sample result
The synthetic sample has 10 MW contracted capacity and four one-hour intervals. Metered availability is 97.5% against a 98.0% target. The supplied contract specifies USD 500 per percentage point shortfall, so the derived penalty is USD 250 and expected payment is USD 9,750. Invoice, settlement and payment each show USD 10,000, producing a USD 250 contract-to-invoice variance.

The incomplete sample returns UNKNOWN: two of four required intervals are missing, so the tool refuses to calculate a complete contractual amount.

## Boundaries
- All fixtures and references are synthetic; no live market or customer data.
- Not an ISO/RTO shadow-settlement engine, dispatch optimizer, trading strategy, accounting assurance, audit opinion or legal interpretation.
- Only implements the explicit illustrative formula in the supplied contract fixture. Real tolling, revenue-share, capacity, energy, ancillary-service and degradation provisions require buyer-approved rules and domain review.
- No connection to meters, SCADA, EMS, market operators, registries, banks or payment rails.
- PASS only means supplied records reconcile under supplied formula; it does not establish source authenticity.
