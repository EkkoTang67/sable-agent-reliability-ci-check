# Claim Confidence & Evidence Weighting v1.0

Status: ACTIVE — decision aid, not a certification  
Budget: 0  
Applies to: product selection, distribution, development, buyer qualification, licensing, and payment claims.

## 1. Core rule

We do not ask whether a person or project is generally “credible.” We score the **specific claim**, the evidence that supports it, and whether that evidence is sufficient for the decision at hand.

A plausible story is not proof. A score is not proof either. The score organizes inspection; it does not turn weak evidence into a verified fact.

## 2. Record one claim at a time

For each consequential assumption, record:

- **Claim:** one falsifiable sentence.
- **Decision affected:** what we would do differently if it were true.
- **Evidence for / against:** direct source links or exact artifacts.
- **Source chain:** who created the evidence and whether multiple reports trace back to the same original.
- **Status:** FACT / INFERENCE / UNKNOWN / DISPROVEN.
- **Evidence score:** 0–10 using the rubric below.
- **Consequence if wrong:** low / medium / high.
- **Cheapest discriminating check:** one action that can change the decision.
- **Decision:** CONTINUE / TEST / PARK / KILL / R3 VERIFIED.

## 3. Evidence strength rubric (0–10)

Score each dimension 0, 1, or 2. Judge the evidence for this claim, not the source's brand reputation alone.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Directness | Opinion, inference, or unrelated proxy | Partial evidence or indirect observation | Directly bears on the exact claim |
| Authority | Unknown / interested / unverifiable source | Identifiable source with limited authority | Authoritative primary source or system-of-record evidence |
| Independence | Repeats the same origin or source chain | Partly independent corroboration | Genuinely independent corroboration |
| Freshness | Stale or timestamp unknown where freshness matters | Date known but freshness uncertain | Current for the decision's required time window |
| Reproducibility | No inspectable supporting artifact | Partly inspectable | Another person can repeat the check or inspect raw evidence |

Interpretation:
- **8–10: strong evidence** for the scoped claim, only if Directness = 2 and no unresolved critical contradiction.
- **5–7: partial evidence** — use for prioritizing the next test, not for asserting certainty.
- **0–4: weak evidence** — keep as INFERENCE or UNKNOWN.

A low score does not prove a claim false. A high score does not prove claims outside the evidence's scope. If the decision depends on a critical binary condition and direct evidence is missing, the status remains UNKNOWN regardless of the total score.

## 4. Do not double-count credibility

- Five pages republishing the same press release count as one source chain, not five independent confirmations.
- Multiple AI summaries of one original document are not independent evidence.
- A platform's own marketing claims can establish what it advertises, not that its performance claims are independently true.
- A buyer saying “interesting” proves interest was expressed, not budget, purchasing authority, intent to pay, or settlement.
- An install or star does not establish useful real-world use.
- A successful local test does not establish production readiness or buyer willingness to pay.

## 5. Confidence is claim-specific

Never write “we are 87% sure” unless we have a calibrated probabilistic model and relevant outcome data. For early-stage research, use the evidence score plus a plain-language status. Do not convert the score mechanically into a probability.

Keep separate:
- **Evidence strength:** how well this artifact supports this claim.
- **Claim status:** what the evidence establishes.
- **Commercial state:** attention / install / verified use / qualified paid intent / payable now / PAID-and-settled.
- **Impact:** how costly it would be to act on a false claim.

## 6. High-consequence and R3 gates

For a high-consequence decision, one unverified critical condition must remain UNKNOWN and block the claim from being upgraded to FACT.

For commercial opportunities, assess the gates separately:
1. Real current economic event.
2. Decision and deadline.
3. Material consequence.
4. Decision owner.
5. Buyer and payer identity/authority.
6. Payable path and terms.
7. Independent evidence can change the decision.
8. Bypass test: can the target proceed without us?
9. Actual payment and settlement evidence.

Do not average away a missing gate. A high evidence score on market demand cannot compensate for an unknown payer. An invoice or payment attempt cannot compensate for missing settlement evidence. R3 requires a lawful, authorized stranger-buyer transaction with verifiable funds actually settled into the user's controlled account.

## 7. Choice rule under uncertainty

Use the smallest test that could falsify the assumption before building more:
- If evidence is weak and the test is free: TEST.
- If the evidence could not change the decision or buyer can bypass the solution: PARK or KILL.
- If the decision matters but essential facts cannot be checked: UNKNOWN; do not market the claim as verified.
- If evidence supports a narrow implementation claim but not its commercial value: retain the technical fact, keep buyer demand UNKNOWN.
- If a real buyer has clear authority, a concrete deadline and a payable path: make one explicit offer; do not treat intent as paid.
- After settlement is independently checked: record R3 VERIFIED for that specific transaction only.

## 8. Anti-self-deception review

Before each weekly decision, ask:
1. What exact observation would prove my current hypothesis wrong?
2. Is this primary evidence, or several retellings of one source?
3. Am I mistaking a technical success for commercial demand?
4. Which critical fact is still UNKNOWN?
5. What is the smallest zero-cost check that can change the next action?
6. What would make us stop?

If no evidence has arrived, report “no new evidence” rather than increasing confidence because time has passed.

## 9. Relationship to the feedback loop

Use this rubric inside [Feedback-to-Cash Loop v1.0](../feedback/FEEDBACK_TO_CASH_LOOP_V1.md). The feedback loop decides how observations feed experiments; this document defines how much a given observation should support a claim.

The governing principle is: **weight evidence by directness, authority, independence, freshness and reproducibility; never weight belief by enthusiasm, repetition, or effort already spent.**
