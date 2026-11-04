# Decision Error Correction System (DECS) v1.0

Status: ACTIVE — operating protocol; manual/AI-assisted until automation is implemented  
Budget: 0 by default  
Objective: reduce time-to-detect, cost-to-correct, and recurrence of consequential decision errors.

## 1. Mission and success criteria

DECS exists to discover wrong assumptions earlier, stop weak decisions before they consume resources, and convert material errors into reusable controls.

Optimize for:
1. Detection latency: time between an assumption becoming false and the system noticing.
2. Correction cost: money, time, attention, reputation, and opportunity cost spent before correction.
3. Recurrence rate: how often the same error class appears again.
4. Decision quality: whether the action was proportionate to evidence available at the time, not whether the outcome was lucky.

Do not optimize for confidence, activity, number of ideas, agents, or documents produced.

## 2. Non-negotiable rules

- Plausibility, repetition, enthusiasm, and AI fluency are not evidence.
- Separate FACT / INFERENCE / UNKNOWN / DISPROVEN / VERIFIED / NOT_VERIFIED / PARKED.
- Every consequential decision must identify what would make it wrong.
- A critical UNKNOWN blocks irreversible action that depends on it.
- Never average away a missing critical gate with a high score elsewhere.
- Prefer the cheapest discriminating test over more discussion, research, or building.
- Stage resource release. Commit only enough to reach the next uncertainty-reducing milestone.
- Set a maximum loss before an experiment. If no affordable loss limit exists, do not run it.
- A failed prediction is useful data. Hiding, rationalizing, or silently rewriting it is a system failure.
- Sunk cost, embarrassment, public commitment, and attachment are not reasons to continue.
- AI must challenge both the operator's assumptions and its own prior outputs.
- Distinguish a good decision from a good outcome. Judge the process using information available at decision time; judge outcomes separately.

## 3. Decision severity

| Level | Examples | Required control |
|---|---|---|
| D0 — trivial/reversible | wording, low-cost exploration | quick check; no formal record |
| D1 — bounded/reversible | free research, small prototype, one outreach test | short record; explicit stop condition |
| D2 — material | public claims, buyer proposal, meaningful time commitment, external data handling | evidence review + adversarial review + staged commitment |
| D3 — high consequence/irreversible | legal commitments, production changes, sensitive data, significant spend, safety, reputation, account/payment risk | independent verification where possible; critical UNKNOWN blocks execution; explicit human authorization |

If uncertain, classify one level higher.

## 4. The nine-step correction loop

### Step 1 — State the decision
Write: “We must decide whether to ___ by ___ because ___.” Record the action at stake. If no action changes based on the answer, this is research, not a decision.

### Step 2 — Atomize assumptions
Split the decision into individually falsifiable claims. For each, record:
- exact claim and scope;
- status: FACT / INFERENCE / UNKNOWN / DISPROVEN;
- evidence for and against;
- source, date, source chain, and directness;
- evidence score using Claim Confidence & Evidence Weighting;
- consequence if wrong;
- owner and next check.

Do not convert an evidence score into a probability.

### Step 3 — Pre-mortem and disconfirmation
Before committing, ask:
1. Assume this decision failed. What are the five most plausible causes?
2. What observation would make us stop immediately?
3. What evidence would a skeptical buyer, operator, auditor, or competitor demand?
4. What is the strongest alternative explanation for the evidence?
5. What are we not measuring?
6. What would change our mind?

The AI reviewer must produce at least one credible kill hypothesis, not generic risks.

### Step 4 — Find the cheapest discriminating test
Choose one test that separates competing explanations. Prefer:
1. existing primary evidence or system-of-record check;
2. direct confirmation from the decision owner, payer, or authorized source;
3. a small, reversible, bounded experiment;
4. a larger experiment only if smaller tests cannot answer the question.

A test is useful only if possible outcomes lead to different actions.

### Step 5 — Set exposure limits before execution
Record maximum cash spend, maximum hours/attention, data/access boundary, maximum attempts, deadline, stop-loss condition, and escalation conditions.

Use staged commitment. Release only enough resources to reach the next decision gate. No automatic budget escalation.

### Step 6 — Execute and preserve raw observations
Record what actually happened, including negative results, missing evidence, delays, refusals, tool errors, and contradictions. Preserve timestamps and source links. Do not replace raw observations with an AI summary; summaries must link to source artifacts.

### Step 7 — Update claim status and decision
- Retain FACT only when directly supported within scope.
- Downgrade to UNKNOWN when evidence is missing, stale, conflicting, or unauthoritative.
- Mark DISPROVEN when direct contradictory evidence defeats the claim.
- Use VERIFIED only for the exact bounded condition tested.
- Keep NOT_VERIFIED distinct from DISPROVEN when the test/evidence was insufficient.

Decision outcomes: CONTINUE / TEST / REDUCE_SCOPE / PARK / KILL / ESCALATE_FOR_HUMAN_AUTHORIZATION.

### Step 8 — Diagnose the error class
Use one or more root-cause tags:
- E1 observation/source error
- E2 stale evidence/timing error
- E3 causal-model error
- E4 probability/base-rate error
- E5 buyer, payer, or authority error
- E6 budget/procurement/eligibility error
- E7 legal, compliance, privacy, or safety error
- E8 payment/settlement/operational-path error
- E9 execution/implementation error
- E10 scope/acceptance-criteria error
- E11 incentive/strategic-behavior error
- E12 cognitive error: confirmation bias, sunk cost, overconfidence, anchoring, narrative fallacy
- E13 AI/tool error: hallucination, stale retrieval, mistaken tool result, unsupported inference
- E14 unknown/mixed cause

For each error, record what we believed, what was observed, why the belief failed, when it could first have been detected, which signal was missed, what control would have caught it, and whether that control is worth its cost.

### Step 9 — Install a reusable correction
A learning is not complete until it changes at least one checklist, decision gate, evidence requirement, resource limit, test, AI instruction, data field, or stop/kill rule.

Do not create a permanent rule for every isolated anomaly. Require recurrence, materiality, or clear preventability before adding process weight.

## 5. Resource protection

Default staged release:
- Stage 0 — OBSERVE: free/near-free evidence collection.
- Stage 1 — DISCRIMINATE: smallest test; minimal time; no irreversible action.
- Stage 2 — VALIDATE: only after the critical hypothesis survives; limited scope and capped spend.
- Stage 3 — COMMIT: only after buyer, authority, acceptance, payment, and legal gates are established where applicable.
- Stage 4 — SCALE: only after repeatability, margin, delivery capacity, and risk are evidenced.

Passing one stage does not automatically authorize the next.

Stop, park, or reduce scope when:
- a critical assumption is disproven;
- evidence cannot be obtained within the predefined cap;
- decision owner or payer cannot be identified;
- budget or purchasing authority is merely inferred;
- legal eligibility, data authorization, or payment path is unresolved for an action that depends on it;
- buyer can bypass the proposed work without material consequence;
- acceptance condition is vague or unobservable;
- experiment exceeds its cash/time/access boundary;
- new evidence materially worsens expected value;
- the only reason to continue is sunk cost, embarrassment, or enthusiasm.

A stop is a successful control when it prevents a larger loss.

## 6. Commercial reality gates

Keep these states separate:

SIGNAL → REAL_EVENT → DECISION_OWNER → BUYER_CONFIRMED → PAYER_CONFIRMED → BUDGET_CONFIRMED → PROCUREMENT_ELIGIBILITY → PAYMENT_PATH_CONFIRMED → PAYABLE_NOW → CONTRACTED → DELIVERED → ACCEPTED → SETTLED

Do not skip states. Public project budget is not subcontract budget. A shortlist is not an award. An award is not a subcontract. A buyer reply is not budget. A quote is not a purchase order. An invoice is not settlement. A payment request created is not money received.

R3 is reached only for a lawful, authorized transaction with a stranger buyer and verifiable funds actually settled into the operator's controlled account.

For cross-border work, independently check individual-vendor eligibility, contract entity, tax/document requirements, data restrictions, insurance, sanctions/export controls where relevant, and the exact receiving rail. A payment provider's ability to create a request does not prove the buyer can or will pay through it.

## 7. Mandatory AI system instructions

When assisting with a consequential decision, the AI must:
1. Identify the exact decision, action, and deadline.
2. Separate facts, inferences, unknowns, and disproven claims.
3. State the source and freshness of each material claim; distinguish primary evidence from repeated reporting.
4. Identify the strongest counter-hypothesis and what evidence would falsify the current recommendation.
5. Identify missing critical gates; never fill them with plausible guesses.
6. Assess downside in cash, time, attention, reputation, legal exposure, data exposure, and lost alternatives.
7. Propose the cheapest test that could change the decision.
8. Set maximum exposure and explicit stop conditions before recommending execution.
9. Give a recommendation with qualitative confidence; keep evidence score separate; never invent calibrated probabilities.
10. After new evidence, compare prediction with observation and update the decision record.
11. Admit when an earlier AI answer was wrong, stale, incomplete, or unsupported; identify the exact correction.
12. Never claim to have searched, contacted, sent, tested, changed, committed, or verified anything unless the relevant action actually returned success.
13. Never treat user confidence, AI fluency, or repetition across agents as evidence.
14. Do not overwhelm the user with more strategy when the next discriminating action is clear.
15. Prefer “UNKNOWN — do not commit yet” over a fabricated answer.

### Required response format for material decisions
- Decision: what must be decided and by when.
- Current verdict: CONTINUE / TEST / REDUCE_SCOPE / PARK / KILL / HUMAN_APPROVAL.
- Facts: directly supported observations.
- Inferences: interpretations, clearly labeled.
- Critical unknowns: unresolved gates that could change the decision.
- Best counter-case: strongest reason the recommendation may be wrong.
- Cheapest discriminating test: exact next check and possible outcomes.
- Exposure cap: cash, hours, access, and deadline.
- Stop conditions: objective triggers.
- Update trigger: new evidence that would change the verdict.

Do not force this format on trivial or purely creative requests.

## 8. Forecast and decision log

For every D2/D3 decision, preserve a timestamped record before the outcome is known:
- decision ID and date/time;
- claim and scope;
- forecast / expected observable result;
- confidence category LOW / MEDIUM / HIGH with rationale, not a fake percentage;
- evidence score and source links;
- consequence if wrong;
- chosen action and rejected alternatives;
- exposure cap and stop condition;
- review date.

At review, record actual outcome, forecast error, root-cause tags, correction, and whether the process was reasonable given information available at the time.

Never rewrite old forecasts. Append corrections with timestamps.

## 9. Metrics

Track monthly:
- median detection latency for material errors;
- median correction cost before stop;
- percentage of D2/D3 decisions with pre-recorded falsifier and exposure cap;
- percentage of critical UNKNOWNs correctly blocking action;
- repeated error rate by root-cause tag;
- percentage of material predictions reviewed against outcomes;
- false-stop rate: valuable opportunities killed without adequate evidence;
- false-go rate: resources committed despite a failed critical gate.

Target direction: detection latency ↓, correction cost ↓, recurrence ↓, false-go ↓, while monitoring false-stop so caution does not paralyze action.

Do not invent numerical targets before a baseline. Establish a baseline from the first 10 material decisions, then set realistic improvement targets.

## 10. Review cadence

- Before each D2/D3 action: pre-mortem, critical unknowns, exposure cap, stop conditions.
- After each test or material signal: update claim status and verdict immediately.
- Weekly (15–30 minutes): review open decisions, overdue checks, contradictions, and stop triggers.
- Monthly: inspect repeated error classes and revise controls; remove controls that add cost without catching material errors.

No daily journaling burden is required. Capture a record when the decision is made; AI should maintain and summarize it.

## 11. Relationship to existing controls

DECS complements, and does not replace:
- Claim Confidence & Evidence Weighting — evaluates evidence for a specific claim.
- Feedback-to-Cash Loop — turns observations into experiments and commercial learning.
- Commercial decision and payment commitment gates — qualify payer, payable-now, and settlement states.

DECS governs how decisions are formed, exposed to risk, tested, corrected, and learned from across the entire AI operating system.

Template: [DECISION_RECORD_TEMPLATE.md](../../templates/decision-quality/DECISION_RECORD_TEMPLATE.md)

**Governing principle: Commit in proportion to evidence. Detect error early. Correct cheaply. Never pay twice for the same lesson.**
