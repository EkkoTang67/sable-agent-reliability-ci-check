# SABLE One-Claim Closure Card v1.1

**One claim. One authorized boundary. One evidence-backed answer.**

SABLE checks whether a specific action produced the required outcome—not just whether the action returned “success.”

## Choose the fixed scope

### US$99 — Micro Closure
One claim, one workflow, one authorized boundary, one bounded check, and one evidence receipt. Use this when the evidence surface is small and the question is precise.

Pay: https://paypal.me/tang665/99USD

### US$299 — Decision Closure
One bounded failure sequence that crosses multiple states or evidence boundaries, such as replay/retry, cancellation races, payment-to-entitlement mismatches, migration/reconciliation, or release provenance.

Pay: https://paypal.me/tang665/299USD

**Not sure which scope fits?** Send the claim and boundary to [SABLE before paying](mailto:sable-verification@agentmail.to?subject=Scope%20fit%20for%20one%20bounded%20SABLE%20check). No discovery call is required.

## Four inputs to start

Copy this and provide only what you know:

```text
PRODUCT: MICRO_CLOSURE or DECISION_CLOSURE
CLAIM: What exact result must be proved?
REFERENCE: Payment/order/job ID, issue, or pinned build/revision (if applicable).
BOUNDARY: The authorized tenant, staging environment, build, workflow, or evidence set.
DECISION: What will this result let you release, accept, refund, reconcile, or stop? Deadline: UTC time or none.
```

Use redacted identifiers. **Do not send credentials, API keys, private keys, personal customer data, or production secrets in email or a PayPal note.** If access is needed, agree on a safe, authorized read-only method or controlled test boundary.

## What you receive

A bounded evidence package containing:

1. The exact claim and authorized boundary.
2. The observed sequence and evidence references.
3. The invariant/check applied to the observations.
4. The verdict and limitations:
   - **VERIFIED** — sufficient evidence supports the claim.
   - **NOT_VERIFIED** — evidence contradicts the claim or the invariant fails.
   - **UNKNOWN** — evidence is missing, stale, conflicting, non-authoritative, or insufficient.
5. A traceable receipt/report identity; a digest is included when the report format supports it.

A positive result is not guaranteed. A failed check is a valid result. A success response is not, by itself, proof of the intended business effect.

## Authorization and execution boundary

Payment starts intake; it does **not** authorize production access or a production write. Before execution, the scope and authority must be confirmed. Tests run only inside the agreed authorized boundary. No live-money operation, unrestricted penetration test, production-wide assurance, legal/accounting certification, or remediation retainer is included.

If the available inputs only repeat the buyer's claim and no independent observation can be obtained, the result must remain **UNKNOWN** or explicitly state the evidence gap.

## One-sentence decision test

> “Before we release, refund, accept, or reconcile this, we need independent evidence that the intended result actually happened.”

If that is not the decision at stake, this is probably not a SABLE closure.
