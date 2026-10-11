# SABLE market wedge: retainage-release evidence closure

**Status:** research hypothesis; not a validated paid opportunity.
**Sector:** commercial construction finance, not AI tooling.
**Target workflow:** a specialty subcontractor's own scope is substantially complete, but a meaningful retainage balance or final payment is blocked by an evidence/closeout question before an upcoming payment application.

## Why this is worth testing

### Public evidence (facts, not proof of a purchase)
1. A public construction-community post dated 2026-06-24 describes a subcontractor with approximately **$50,000 in retainage outstanding for about six months**, with the final 1% of work dependent on general-contractor actions. A later comment says an itemized scope-closeout request with punch sign-off and a date is more actionable than a vague release request. This is one anonymous anecdote, not a representative market estimate.
   Source: https://www.reddit.com/r/Construction/comments/1uehqtf/retainage_stuck_in_the_abyss/
2. Commercial construction software explicitly tracks retainage, lien waivers, pay applications and release milestones. This proves the workflow is real and also signals competitive alternatives.
   Sources:
   - https://builderpad.com/vendor-billing
   - https://www.buildpass.ai/us/features/finance/pay-applications
3. Construction-specialist accounting firms sell recurring financial operations, retainage tracking and subcontractor/lien-waiver management. Published price points span roughly $500–$2,500+/month for some service tiers, but these are not prices for SABLE and do not prove demand for this offer.
   Sources:
   - https://www.buildercfo.co/services
   - https://www.finriseadvisors.com/services

## The narrow wedge

**Retainage Release Readiness Pack** — a case-level evidence map for a subcontractor whose own scope is complete but whose retainage/final-payment decision is blocked by a specific document or status uncertainty.

Not another retainage tracker. Not legal services. Not debt collection. Not a guarantee of release.

The pack maps the customer's own closeout checklist to the evidence they provide and returns:
- requirement-by-requirement status: PRESENT / MISSING / CONFLICTING / UNCLEAR;
- source/document references for each status;
- dated event chronology from the submitted records;
- explicit blockers and unanswered questions;
- a neutral draft request for the customer's authorized reviewer to edit and send;
- a hash-indexed evidence manifest.

SABLE's proof kernel is reused: claim → authorized boundary → observations → invariant/check → verdict → evidence. The underlying tool stays generic; the offer and evidence schema are industry-specific.

## Best initial buyer / route

Primary economic beneficiary: a specialty subcontractor owner, controller or AR lead with a materially sized retainage balance (test threshold: at least $25,000) tied to the subcontractor's own completed scope.

Potential channel buyer: construction-focused bookkeeping/fractional-CFO firms already tracking retainage across multiple clients. Their incentive is to reduce manual exception-chasing and offer a discrete, evidence-based add-on without replacing their accounting service.

First channel hypothesis to test: FinRise Advisors, which publicly offers construction accounting, AIA billing, retainage tracking and lien-waiver management to US businesses, and publishes contact information at https://www.finriseadvisors.com/services. This is a prospect, not a confirmed partner or buyer.

## Proposed bounded pilot (test price, not market-validated)

**US$750 per case** for one subcontractor scope, one payment/retainage decision, customer-provided release checklist, up to 25 redacted evidence files, one evidence matrix + chronology + gap list + draft operational request. Deliver within 3 business days after complete inputs and written scope confirmation.

Price only proceeds if the buyer confirms the case is live, the held amount is material, the decision deadline is real, and the buyer has payment authority. Do not discount the price to disguise missing demand. If no one accepts a paid pilot, revise or kill the offer.

## Hard safety/legal/data boundaries
- Use redacted documents for the first pilot; do not request bank credentials, tax IDs, customer personal data, private keys, or access to accounting/project systems.
- Customer supplies the governing checklist and identifies which contract clauses or requirements must be checked. We check document presence, consistency and source links; we do not decide legal entitlement, interpret statutory rights, advise on lien strategy, certify completion, or contact a GC as the customer's representative.
- Customer's authorized professional makes all legal, commercial and release decisions and sends any request.
- No production system writes, payment initiation, legal claims, lien filings, fund custody or guarantee of payment.
- Encrypt/store no client data beyond the agreed handling window; if safe handling cannot be provided, stop before receiving documents.
- Quote, scope, evidence basis and exclusions in writing before payment/work.

## Buyer qualification gate
Proceed only when all answers are yes:
1. Is there a current retainage/final-payment item, not a hypothetical workflow?
2. Is at least $25,000 currently held or otherwise materially consequential?
3. Is the subcontractor's own scope complete or near-complete?
4. Is a specific evidence/status UNKNOWN blocking a near-term decision?
5. Can independent evidence plausibly change the next action?
6. Is a named owner/controller/CFO the decision owner and payer, or is a specific channel firm authorized to pay?
7. Can the buyer lawfully share a redacted evidence set?
8. Is there a valid payment route and a willingness to pay US$750 for the bounded case?

Any missing answer = ROUTE_TO_PAYER / NOT_READY. If the cause is another party's unfinished work rather than an evidence gap, kill the case.

## 7-day experiment and stop rules
- Day 1: use one public sample case to show the exact report shape, clearly marked synthetic.
- Day 1–2: approach up to 5 highly relevant construction accounting / subcontractor finance operators with one specific paid-pilot ask. No mass mail.
- Day 3–5: qualify responses on case, amount held, deadline, payer, budget, and evidence gap; do not build integrations.
- Day 6–7: deliver only if one paid, authorized, redacted pilot exists. Otherwise record R3=0 for this experiment and decide whether to change segment or kill it.
- Success requires settled funds in an account the seller controls, not reply, interest, meeting, or promise.

## Current ledger
- FACT: public sources describe retainage being held and the workflow/tool category exists.
- INFERENCE: an exception-only evidence pack may help a subcontractor finance operator or accounting partner resolve a specific documentation blocker.
- UNKNOWN: the frequency of eligible cases, the willingness to pay US$750, a buyer with current need, the ability to make a legal cross-border payment to the seller, and whether the offer performs better than the buyer's internal process.
- PAID / R3: none.
