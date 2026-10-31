# SABLE Evidence Workbench v0.1

A shared deterministic engine for buyer-authorized evidence preflight across different vertical workflows. The first two synthetic adapters are cargo claims and overseas equipment warranty cases.

## Design rule

**One engine; buyer-approved vertical rules; one evidence receipt format.**

The engine does not decide insurance coverage, liability, technical cause, warranty entitlement, repair approval, or payment. It checks only explicitly supplied fields against the buyer's written rule set.

## Run the demos

From the repository root:

```bash
python3 workbench/evidence_workbench.py workbench/samples/cargo_claims.synthetic.json --json-out /tmp/cargo-report.json --markdown-out /tmp/cargo-report.md
python3 workbench/evidence_workbench.py workbench/samples/equipment_warranty.synthetic.json --json-out /tmp/warranty-report.json --markdown-out /tmp/warranty-report.md
python3 -m unittest discover -s workbench/tests -p 'test_*.py' -v
```

The fixtures intentionally include PASS, GAP and UNKNOWN cases. All identities, source references, values and events are fictional.

## Canonical input

- `engagement_id`: bounded buyer-authorized work package.
- `domain`: cargo_claims or equipment_warranty.
- `buyer_rule_version`: exact version supplied/approved by the buyer.
- `cases[]`: individual claims or warranty cases.
- `records[]`: normalized source-record extracts with record IDs, source references and fields.
- `checks[]`: explicit buyer-approved checks referring to record IDs and fields.

Supported v0.1 check types:
- `required`: one field must be present.
- `same`: two or more referenced values must match.
- `date_order`: first ISO date must be on or before the second.
- `numeric_equal`: numeric values must agree within a buyer-specified tolerance.

Unsupported or ambiguous rule types fail input validation rather than being silently guessed.

## Verdict semantics

- `PASS`: all declared checks passed.
- `GAP`: at least one declared check found a conflict or failed condition, and none is UNKNOWN.
- `UNKNOWN`: at least one check cannot be evaluated because a record/field is missing or malformed. UNKNOWN takes precedence in the overall verdict so incomplete evidence cannot be presented as a clean pass.

Each check records its observed values and source references. The report includes the exact input SHA-256 digest for reproducibility.

## What v0.1 does not do

- No PDF/OCR, email ingestion, image analysis or automatic document authenticity checks.
- No legal interpretation, coverage/entitlement determination, engineering diagnosis, loss adjustment or approval.
- No external system, insurer, carrier, OEM, bank, registry or payment integration.
- No claim that the supplied source records are authentic or complete.
- No production readiness or security certification claim.

The first commercial trial should use buyer-authorized, minimized structured extracts or buyer-prepared text/CSV/JSON. Original documents and systems remain in the buyer's approved environment unless a separately approved data-processing arrangement says otherwise.

## Buyer acceptance checklist

Before work starts:
1. Buyer names the decision owner, payer, acceptance owner and authorized data owner.
2. Buyer supplies and versions the checklist/rules; each check has a named business meaning.
3. Buyer confirms subcontractor eligibility, data-processing location, retention/deletion, confidentiality and lawful payment route.
4. Buyer supplies a masked or synthetic dry-run first; no unapproved customer data is transferred.
5. Both sides agree the case count, included record types, correction pass and exclusions.

Acceptance:
1. Every input case appears exactly once in the report.
2. Every check has a deterministic PASS/GAP/UNKNOWN result.
3. Every result identifies the source references and observed values used.
4. Missing evidence remains UNKNOWN; no inferred value is inserted.
5. Buyer-provided known-positive, known-conflict and known-missing test cases produce the agreed expected results.
6. Re-running the same input and rules produces the same verdicts and input digest.
7. Buyer reviews and signs off the exception register; the workbench does not make the final professional or legal decision.

## Commercial boundary

This is a reusable delivery tool, not a product-market-fit claim. No live customer data, paid deployment, customer saving, recovered claim, accepted purchase order or revenue is represented here. A template becomes a delivery configuration only after a real buyer confirms the workload, rules, data boundary, payer and acceptance criteria.
