# SABLE Product Mechanics — Buyer-Ready Contract v3.3

## Buyer-facing promise

**Your system says it worked. We check the real result.**

SABLE closes a concrete, bounded outcome question against an authorized boundary and the best available independent evidence.

## Commercial offers

### US$99 — Micro Closure
- One claim.
- One workflow.
- One explicitly authorized boundary.
- One bounded check.
- One evidence receipt.

### US$299 — Decision Closure
- One bounded failure sequence across multiple states or evidence boundaries.
- Suitable for replay/retry, cancellation races, payment-to-entitlement reconciliation, migration/reconciliation, or release/revision provenance.

Payment links:
- US$99: https://paypal.me/tang665/99USD — PayPal note: `PRODUCT=MICRO_CLOSURE` + a short claim/reference.
- US$299: https://paypal.me/tang665/299USD — PayPal note: `PRODUCT=DECISION_CLOSURE` + a short claim/reference.

Never include credentials, private keys, or private customer data in a payment note.

## Minimum claim contract

`claim + decision + consequence + boundary + expected invariant + observation source`

The buyer supplies the exact result that must hold and the scope they are authorized to expose. SABLE must not invent budget, authority, urgency, customer loss, or a failure probability.

## Verification contract

1. Pin the claim and candidate revision/configuration.
2. Confirm the explicit authorized boundary.
3. Execute only the agreed bounded check, or independently examine the agreed evidence set.
4. Observe the best available source of record.
5. Check identity/correlation, freshness, authority, state transition, and the declared invariant as applicable.
6. Return VERIFIED / NOT_VERIFIED / UNKNOWN with evidence references and limitations.

## Trust boundaries

- A success log or HTTP 2xx does not establish a business effect by itself.
- A final state does not necessarily establish correct history; replay/retry cases may require sequence evidence.
- A caller-supplied observation is not automatically authoritative.
- A synthetic fixture is not customer or provider evidence.
- Authenticated endpoint identity does not by itself prove provider signature, effective permissions, or authority over the particular claim.
- The receipt digest establishes content identity only; it is not a digital signature or proof of authorship.
- If the evidence cannot support the claim, return UNKNOWN or explicitly record the evidence gap.

## Operational limits

SABLE does not currently claim a universal live-provider adapter or production-wide integration. Each paid engagement requires a feasible observation path, authorized access, a fixed scope, and truthfully stated tool boundaries. No test begins until scope and authorization are confirmed.

The commercial unit is a decision-relevant evidence closure, not a promise of green checks.
