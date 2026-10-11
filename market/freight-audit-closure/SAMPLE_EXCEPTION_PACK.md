# SABLE Exception Evidence Closure Pack
## Synthetic sample — no real customer, carrier, invoice, contract or shipment

**Purpose:** show what an auditor receives after they have already flagged a possible billing exception.
**Not a freight audit opinion.** No legal/contractual recovery entitlement is established here.

## Executive handoff
- Candidate exceptions reviewed: 3
- SUPPORTED as a data/math observation: 1
- INCOMPLETE: 1
- CONFLICT: 1
- Confirmed recoverable amount: **not calculated**
- Production records queried: none

## Exception matrix

| Case | Candidate issue supplied by auditor | Evidence present | Verdict | Reviewer action |
|---|---|---|---|---|
| EX-001 | Same PRO appears on two invoice records | Invoice A + Invoice B show matching PRO SYN-PRO-1042 and same stated charge | CONFLICT | Confirm whether documents are duplicate billings, rebills, or adjustments before making a claim |
| EX-002 | Contract line rate differs from invoice | Redacted rate excerpt says $850.00; synthetic invoice line says $1,035.00; arithmetic variance $185.00 | SUPPORTED (arithmetic only) | Contract applicability, effective date, lane, freight class and accessorial basis remain for authorized reviewer to confirm |
| EX-003 | Liftgate accessorial potentially not performed | Invoice lists $145.00 liftgate; no shipment/dispatch evidence attached | INCOMPLETE | Obtain proof of service or dispatch record before classifying it as inapplicable |

## Source-provenance example (synthetic)

### EX-002
- Invoice: SYN-INVOICE-2026-008, page 2, line 7.
- Rate excerpt: SYN-CONTRACT-REDUCED-03, row 12.
- Invoice amount: USD 1,035.00.
- Rate excerpt amount: USD 850.00.
- Arithmetic difference: USD 185.00.
- Calculation: 1,035.00 - 850.00 = 185.00.
- Evidence verdict: **SUPPORTED (arithmetic only)**.
- Not established: that the quoted rate applied to this shipment, that no surcharge applied, that a claim is timely, or that the carrier must refund USD 185.00.

## Evidence boundary
This pack distinguishes:
1. Whether two records show the same identifier or conflicting values.
2. Whether submitted numbers recalculate correctly.
3. Whether a required evidence artifact is absent.
4. Whether the claim has contractual, operational or legal merit.

SABLE can help with the first three when source documents are supplied. It must not silently infer the fourth.

## Potential buyer acceptance criteria
- Every status links to an exact source, page/row, and hash where available.
- Every arithmetic conclusion can be reproduced.
- Missing evidence is called out instead of filled in by assumption.
- The reviewer can reproduce the report from the same redacted input package.
- Pack materially reduces the buyer's measured review time or rework; if not, do not sell a recurring subscription.

All data on this page are fabricated for demonstration.
