# BRL v1.0 — Buyer Reality Lens

**Purpose:** identify transactions that can be won and paid, not merely markets that sound attractive.

**Operating rule:** do not infer buyer demand from industry growth, a supplier's public contract, a competitor's price list, or a friendly reply. Record observable buyer behavior, preserve uncertainty, and reject an opportunity when a hard purchase condition is missing.

## 1. Decision unit

Research one **specific economic event and one work package**, not an industry or generic buyer persona.

The record must answer:
1. What has happened in the buyer's business now?
2. What decision or deliverable must be completed, by when?
3. What is the consequence of delay, failure, or doing nothing?
4. Who currently performs the work, and what is demonstrably missing?
5. Who owns the problem, approves scope, accepts the result, authorizes spend, and releases payment?
6. What precisely can an external supplier deliver, and how will it be accepted?
7. Why is an unknown individual a credible, lower-risk choice than the buyer's existing alternatives?
8. Is the supplier legally eligible, permitted by the buyer, and able to contract and receive cleared funds through a verified route?

Do not assume one person holds all decision rights. Distinguish the user, technical evaluator, budget owner, procurement/onboarding gatekeeper, acceptance authority, and payer.

## 2. Evidence labels

- **FACT** — directly supported by a primary source or explicit buyer statement; cite source and date.
- **INFERENCE** — reasoned conclusion based on stated facts; show the bridge from facts to conclusion.
- **UNKNOWN** — material information not established. Never fill it with a guess.
- **NOT_VERIFIED** — a verification attempt did not establish the claim.
- **DISPROVEN** — reliable evidence contradicts the claim.
- **SELF_REPORTED** — the seller or buyer states it, but independent corroboration is absent.

Keep commercial claims, procurement status, eligibility, and payment status separate. A posted price is not a paid invoice; an awarded ceiling is not cash collected; a successful message API call is not delivery; a positive reply is not purchase intent.

## 3. Evidence states

- **E0 — Hypothesis:** plausible problem, no concrete external evidence.
- **E1 — External signal:** public project, tender, hiring signal, product offer, or other evidence that the category exists.
- **E2 — Need confirmed:** a named buyer or authorized representative confirms a current task or gap.
- **E3 — Quote-ready:** scope, decision authority, budget/spend authority, acceptance criteria, supplier eligibility, contracting and payment route have been verified.
- **E4 — Commercial commitment:** enforceable contract, purchase order, or equivalent documented commitment.
- **R3 — Settled payment:** funds have cleared into an account controlled by the supplier.
- **REPEATABLE — Repeat purchase:** a second cleared payment, or clear and credible evidence of a repeated buying process. Do not claim repeatability from a single transaction.

A lead can have a large budget and still remain E1. Never promote evidence state by narrative.

## 4. PAYABLE-NOW hard gate

An opportunity is **PAYABLE-NOW** only when all six questions are supported by evidence:

1. Is a specific task currently real?
2. Is there a deadline or material economic consequence?
3. Have we identified the person or process that can authorize the purchase?
4. Is a measurable deliverable and acceptance test agreed or realistically available?
5. Is a specific gap in the incumbent/internal alternative confirmed, and is there a reason to use us?
6. Are eligibility, contracting, invoicing and the actual payout route viable for the supplier's real legal/tax status and location?

If any answer is UNKNOWN, the opportunity is not PAYABLE-NOW. Work only on the missing fact; do not create demos or perform free samples before that gate is passed.

## 5. Buyer economics and game-theory record

For every E2+ lead, record:
- Buyer's objective and downside risk.
- Incumbent and other outside options.
- Cost and effort to switch to us.
- Buyer's verification cost and our proof cost.
- Who bears the risk of a failed test, late delivery, or disputed acceptance.
- What credible commitment makes our offer safer than the alternative.
- Whether the same buyer can buy again and what causes that repeat.
- The buyer's incentive to share scope/access accurately, and ours to avoid overclaiming.

Prefer an offer that is narrower, testable, reversible, and cheaper to verify than a broad promise. Never claim independence when the paying party's incentives or the scope do not support it.

## 6. Distinguish two services

**Overflow execution / evidence preparation:** the payer is an implementation provider that needs extra capacity to complete a task already inside its delivery contract. Sell execution, coverage, reproducibility, or documentation. Do not call the work independent third-party assurance unless the relationship and independence are explicit and accepted by the end buyer.

**Independent acceptance validation:** the payer or final decision-maker accepts the verifier's independence, scope, access, and conflict disclosures. The verifier does not let the producer approve its own result. The evidence can support a decision; it is not automatically certification or regulatory approval.

Do not blur these into one generic “AI QA” offer.

## 7. Approved evidence sources and channel rules

Prioritize:
1. Formal request for proposal / procurement notices and their source documents.
2. Publicly documented contract awards, framework eligibility and open subcontract opportunities.
3. Buyer-owned product, partner, onboarding, or supplier portals that explicitly invite applications.
4. Direct statements from a decision owner in a channel where the buyer has invited contact or the platform permits it.
5. Independent evidence of completed work and actual payment, when available.

A public award proves an award, not an unallocated subcontract. A vendor's service page proves a public offer, not that a customer purchased it. A partner program proves an invitation to discuss partnership, not a funded assignment.

Do not use AgentMail for cold outreach; its published policy does not permit unsolicited cold outreach. Do not evade channel limits by rotating inboxes or switching tools. Use opt-in, invitation, procurement, or explicitly permitted channels.

## 8. Opportunity record template

```yaml
id:
as_of:
buyer:
payer:
economic_event:
source_urls: []
facts: []
inferences: []
unknowns: []
current_task:
deadline:
consequence_if_unresolved:
incumbent_alternatives:
confirmed_gap:
decision_owner:
budget_authority:
acceptance_authority:
deliverable:
acceptance_test:
supplier_eligibility:
contracting_route:
payment_route:
risk_and_conflicts:
evidence_state: E0
payable_now: false
next_verification_action:
kill_or_park_rule:
```

## 9. Required decision output

Every research run ends in one of these outcomes:
- **PURSUE:** all PAYABLE-NOW gates passed; next step is a defined quote or authorized proposal.
- **VERIFY ONE FACT:** one specific unknown prevents progression; identify the cheapest permitted way to verify it.
- **PARK:** potentially real, but no current task, no available authority, no confirmed budget or no near-term route.
- **KILL:** contradicted, closed, ineligible, non-economic, or only narrative without a path to a transaction.

Never finish with “the market is promising” as the decision.

## 10. Priority order

**Settled payment → committed buyer → confirmed task → acceptance proof → evidence asset → product architecture → narrative.**

For first revenue, a small paid, authorized, verifiable delivery beats a large theoretical market. For infrastructure ambitions, repeat purchases and integration into consequential workflows must be demonstrated, not assumed.
