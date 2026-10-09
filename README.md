# SABLE — Your system says it worked. We check the real result.

SABLE checks whether a claimed payment, refund, order, entitlement, release, or AI-agent action reached the required real-world state.

**First use case: Payment went through. Did the customer actually get the correct access or delivery?**

A success message is not the same as a proven outcome. SABLE binds one exact claim to authorized evidence from the relevant system of record and returns one of three verdicts:

- **VERIFIED** — the required outcome is supported by the evidence.
- **NOT_VERIFIED** — the evidence contradicts the claim.
- **UNKNOWN** — the evidence is missing, stale, conflicting, or not authoritative enough.

**The technical boundary:** the action system reports; the system of record answers. SABLE produces a bounded, reviewable evidence receipt. It does not claim universal exactly-once execution or production certification.

## Run the synthetic example

```bash
python3 scripts/sable_proof_gated_settlement.py \
  --file examples/proof-gated-settlement.json \
  --out proof-gated-settlement-report.json
```

This checks the observations in the supplied fixture; it does not independently query a real payment provider by itself. The example is synthetic, not a customer result.

- [SABLE Outcome Proof Layer strategy and differentiation](docs/strategy/SABLE_OUTCOME_PROOF_LAYER_V1.md)
- [Proof-Gated Money Movement specification](PROOF_GATED_MONEY_MOVEMENT_V1.md)
- [Payer-ready Payment Closure Card](docs/buy/SABLE_PAYMENT_CLOSURE_CARD_V1.md)
- [Synthetic payment-closure report](examples/payment-closure-report.json)
- [Proposed portable outcome-receipt schema](schemas/outcome_proof_receipt_v1.schema.json)
- [Synthetic outcome-proof receipt example](examples/outcome-proof-receipt-v1.synthetic.json)

---

## Buy the bounded check

**Your system says it worked. We check the real result.**

### US$99 — Micro Closure

One claim · one workflow · one authorized boundary · one bounded check · one evidence receipt.

Use it for a narrow acceptance condition, payment/order/outcome binding, a single entitlement boundary, or another precise claim with a small evidence surface.

**[Pay US$99 and start →](https://paypal.me/tang665/99USD)**

PayPal note: `PRODUCT=MICRO_CLOSURE` + a short claim/reference. No secrets or customer data.

### US$299 — Decision Closure

One bounded failure sequence across multiple temporal states or evidence boundaries, such as replay/retry, cancellation races, payment/entitlement reconciliation, migration integrity, or release/revision provenance.

**[Pay US$299 and start →](https://paypal.me/tang665/299USD)**

PayPal note: `PRODUCT=DECISION_CLOSURE` + a short claim/reference. No secrets or customer data.

**Not sure which scope fits?** Send only the claim and authorized boundary before paying; no meeting is required: [confirm scope fit](mailto:sable-verification@agentmail.to?subject=Scope%20fit%20for%20one%20bounded%20SABLE%20check&body=CLAIM%3A%20%0ABOUNDARY%3A%20%0ADECISION%3A%20%0A).

### What the buyer receives

A pinned scope, observed evidence and source references, the invariant/check applied, a verdict (**VERIFIED / NOT_VERIFIED / UNKNOWN**), and explicit limitations or evidence gaps. A report digest is included when the receipt format supports one.

### Before execution

Payment starts intake; it does not grant system access or authorize production writes. The exact claim, safe boundary and authority must be confirmed before execution. Do not send secrets, credentials, private keys or private customer data in a payment note or email.

[See the one-claim intake card](docs/buy/SABLE_PAYMENT_CLOSURE_CARD_V1.md) · [See the clearly synthetic receipt example](examples/micro-closure-receipt.md) · [Inspect the source](https://github.com/socksninja/sable-agent-reliability)

## Code entry

After payment, provide these four inputs:

~~~text
CLAIM
The exact outcome that must be proved.

BOUNDARY
The authorized environment / tenant / build / workflow.

ACTION
The bounded action that creates the state transition.

VERIFY
The independent observation or assertion that checks the effect.
~~~

The executable interface is intentionally this small:

~~~bash
python3 scripts/sable_evidence_gate.py \
  --claim "Replay does not create a second entitlement" \
  --boundary "authorized staging tenant" \
  --action "./run-replay.sh" \
  --verify "./verify-entitlement.sh" \
  --out sable-evidence-receipt.json
~~~

For temporal/economic cases, add a bounded specification:

~~~bash
python3 scripts/sable_evidence_gate.py \
  --claim "One authorized payment intent produces exactly one financial effect" \
  --boundary "authorized staging payment flow" \
  --action "./run-payment-replay.sh" \
  --verify "./verify-payment-ledger.sh" \
  --temporal-spec examples/temporal-payment-replay.json \
  --require-temporal-verified \
  --out sable-evidence-receipt.json
~~~

**No production mutation is implied. Execution is authorized, bounded, and evidence-backed.**

## The smallest decision unit

One SABLE closure is:

**1 claim + 1 authorized boundary + 1 temporal/failure sequence + 1 observable outcome + 1 evidence package**

A correct terminal state does **not** prove a correct history.

Example:

~~~text
submit → effect = 1
replay  → effect = 2
reconcile → effect = 1
~~~

The final state looks correct. The history violated the invariant.

SABLE returns **NOT_VERIFIED**, not a false green.

## What SABLE is not

SABLE is **not** a generic QA service, broad penetration test, production-wide assurance, legal/accounting certification, or retainer.

The architecture exists to execute a concrete closure. **The architecture is not the product.**

## SABLE Continuity Principle

SABLE is designed for technological replacement without loss of reality.

> **Technology can change faster without making reality, memory, causality, accountability, and human connection easier to erase.**

This is SABLE's enduring principle:
- **change ≠ progress**
- **new state ≠ better state**
- **automation ≠ progress**
- **claimed outcome ≠ observed outcome**

The implementation may change from human workflow to AI agent, from manual payment to agentic commerce, or from one platform to another. The proof kernel remains:

**CLAIM → BOUNDARY → OBSERVATION → INVARIANT → VERDICT → EVIDENCE**

For consequential change, SABLE asks:

**What changed? What caused it? Who authorized it? What consequence followed? What evidence survives the next replacement?**

This principle does not replace the commercial gate. It gives the system a stable core while the shell evolves.

See [SABLE Continuity Principle — Hard Override v1.0](docs/SABLE_CONTINUITY_PRINCIPLE_HARD_OVERRIDE_V1.md).

## Three-minute technical model

For a provider-neutral workflow:

```text
DECLARED CLAIM
     ↓
AUTHORIZED EXECUTION BOUNDARY
     ↓
ADVERSARIAL TEMPORAL SCENARIO
     ↓
SYSTEM-OF-RECORD OBSERVATIONS
     ↓
ECONOMIC / AUTHORIZATION INVARIANTS
     ↓
VERIFIED / NOT_VERIFIED / UNKNOWN
     ↓
EVIDENCE RECEIPT
```

Current temporal operators include:

- same-intent retry
- same-payload replay
- duplicate callback
- out-of-order event
- crash after external effect
- timeout followed by retry

Current invariant families include:

- exactly-once effect
- effect-ledger uniqueness
- field equality
- field unchanged on replay
- authorized effect
- authorization → effect causal binding
- amount conservation
- allowed state transitions
- required sequence order
- timestamp order

## Run it

### Operational opportunity gate

```bash
python3 sable_operational_opportunity.py \
  --file examples/operational-opportunity.json
```

A weak or non-decision-blocking opportunity is rejected rather than promoted into a commercial target.

### Temporal economic integrity

```bash
python3 sable_temporal_economic_integrity.py \
  --file examples/temporal-payment-replay.json
```

### Adversarial scenario generation

```bash
python3 sable_adversarial_temporal_scenarios.py \
  --file examples/adversarial-temporal-scenarios.json
```

### Explicit action → observation sequence

```bash
python3 sable_temporal_sequence.py \
  --file examples/temporal-payment-sequence.json
```

## GitHub Action

SABLE can be used inside an existing CI/release boundary:

```yaml
- uses: socksninja/sable-agent-reliability@main
  with:
    claim: "Replay does not create a second entitlement"
    boundary: "authorized staging tenant"
    action: "./run-replay.sh"
    verify: "./verify-entitlement.sh"
    temporal_spec: "examples/temporal-payment-replay.json"
    require_temporal_verified: "true"
```

The receipt binds the declared claim, execution result, temporal evidence, provenance-related fields, and hashes.

The top-level verdict now distinguishes a failed assertion from an evidence/execution gap:

**VERIFIED** — the declared verification completed successfully.

**NOT_VERIFIED** — the observed invariant or verification assertion failed.

**UNKNOWN** — the bounded action or required evidence did not complete sufficiently to support either conclusion.

This prevents an infrastructure failure from being reported as proof that the customer's claim was false.

For higher-trust closures, v0.6 can also record an explicit verifier role, independence basis, and provenance references:

```bash
python3 scripts/sable_evidence_gate.py \
  --claim "One authorized payment produces exactly one financial effect" \
  --boundary "authorized staging payment flow" \
  --action "./run-check.sh" \
  --verify "./verify-check.sh" \
  --verifier-role "independent verifier" \
  --independence-basis "verification is separate from the change author" \
  --provenance "commit:<sha>" \
  --require-independence-context
```

Evidence strength is also exposed as an **Evidence Assurance Level**:

- **E1** — bounded action + verification.
- **E2** — E1 + before/after observations.
- **E3** — E2 + verified temporal invariant.
- **E4** — E3 + decision context + independence basis + provenance.

The level is evidence-derived, not a confidence claim, and never implies PAID/R3.

See [SABLE Evidence Quality Standard v1.1](docs/SABLE_EVIDENCE_QUALITY_STANDARD_V1.md).

## Decision-Critical UNKNOWN Rescue v1.0

SABLE now has a distinct **Decision Rescue** layer for moments when a real economic decision is blocked by one unresolved UNKNOWN.

The commercial question is not “who needs verification?” It is:

> **Who must decide something consequential now, but cannot safely move money, goods, access, acceptance, payout, retry, or close because the current evidence is insufficient?**

Decision Rescue modes:

- **PROVE_RELEASE** — can money, escrow, goods, access, or a deployment be released?
- **PROVE_REFUND** — did the refund actually reach the intended economic state?
- **PROVE_RETRY** — is it safe to retry or charge again without a duplicate effect?
- **PROVE_CLOSE** — can the economic state be closed or reconciled?
- **PROVE_ACCEPT** — can the delivered result be accepted?
- **PROVE_PAYOUT** — can an earned payout be released?
- **PROVE_AUTHORIZATION** — was the consequential action within the authority granted for it?

Run the deterministic qualification gate:

```bash
python3 scripts/sable_decision_rescue_gate.py \
  --file examples/decision-rescue-refund.json
```

It returns **KILL / ROUTE_TO_PAYER / NOT_PAYABLE_NOW / PAYABLE_NOW**.

A target must establish:

```text
REAL ECONOMIC EVENT
        ↓
CURRENT DECISION
        ↓
CRITICAL UNKNOWN
        ↓
DECISION OWNER
        ↓
ECONOMIC CONSEQUENCE
        ↓
DECISION DEADLINE
        ↓
INDEPENDENT EVIDENCE CAN CHANGE THE DECISION
        ↓
NON-BYPASSABLE
        ↓
PAYER + PAYMENT AUTHORITY
        ↓
PAYABLE NOW
```

The bypass test explicitly rejects cases that can reasonably be delayed, verified internally, accepted as risk, or worked around.

### $99 Decision Rescue

The default cold-start offer is now:

> **$99 Decision Rescue — one real, bounded, decision-critical UNKNOWN.**

Lead with the decision, not the architecture:

> **Can this refund be closed?**

> **Can this money be released?**

> **Is it safe to charge again?**

> **Can finance close this item today?**

SABLE then returns **VERIFIED / NOT_VERIFIED / UNKNOWN** with evidence.

The architecture remains the mechanism. **The blocked decision is the product.**

See [SABLE Decision Rescue v1.0](docs/SABLE_DECISION_RESCUE_V1.md).

## Commercial gate

SABLE's commercial system rejects the common false positives:

```text
DETECTED
  ↓
BUYER-CONFIRMED
  ↓
DECISION-BLOCKING
  ↓
PAYER-CONFIRMED
  ↓
PAYABLE-NOW
  ↓
PAID
```

A reply is not payment.
An approval is not payment.
An invoice is not payment.
A promise is not payment.

**R3 means verifiable funds received by the seller.**


## Commercial Decision Closure Gate v1.0

A technical UNKNOWN is not automatically a commercial opportunity.

Before a commercial ask, SABLE can now require an explicit chain:

```text
CURRENT DECISION
      ↓
DECISION OWNER
      ↓
ECONOMIC CONSEQUENCE
      ↓
BYPASS TEST
      ↓
EVIDENCE NECESSITY
      ↓
PAYER
      ↓
PAYMENT AUTHORITY
      ↓
PAYABLE NOW
      ↓
PAYMENT PATH
```

The machine gate returns:

**KILL** — the decision chain is incomplete or the UNKNOWN can reasonably be bypassed.

**ROUTE_TO_PAYER** — the decision is real, but payer or payment authority is unconfirmed.

**NOT_PAYABLE_NOW** — the payer chain exists, but payment cannot execute now.

**PAYABLE_NOW** — the target is ready for one explicit payment ask.

Run:

```bash
python3 scripts/sable_commercial_decision_gate.py \
  --file examples/commercial-decision-closure.json
```

To make commercial readiness a hard precondition for an Evidence Gate run:

```bash
python3 scripts/sable_evidence_gate.py \
  --claim "One authorized action produces exactly one financial effect" \
  --boundary "authorized staging workflow" \
  --action "./run-check.sh" \
  --verify "./verify-check.sh" \
  --commercial-decision examples/commercial-decision-closure.json \
  --require-commercial-decision-closure
```

The Evidence Gate receipt records the commercial qualification and explicit context. **It never infers PAID or R3.**

See [SABLE Commercial Decision Closure v1.0](docs/SABLE_COMMERCIAL_DECISION_CLOSURE_V1.md).


## Perception–Reality Gap

SABLE also closes **Perception–Reality Gaps**: cases where a user, agent, or interface perceives a consequential state that does not match the authoritative observed reality.

```
PERCEIVED / DECLARED STATE
        ↓
CONSEQUENTIAL ACTION
        ↓
AUTHORITATIVE OBSERVATION
        ↓
VERIFIED / NOT_VERIFIED / UNKNOWN
```

An explicitly authorized, isolated test may introduce a bounded false-success or ambiguous-success signal to measure whether the decision layer verifies reality instead of trusting the signal.

Run the gate:

~~~bash
python3 scripts/sable_perception_reality_gate.py \
  --file examples/perception-reality-refund.json
~~~

See [SABLE PERCEPTION–REALITY GAP v1.0](docs/SABLE_PERCEPTION_REALITY_GAP_v1.0.md).

The test is never authorization to deceive uninvolved users or mutate production systems without explicit approval.

## Mispricing Hunt

**Mispriced certainty** is now a first-class SABLE target: a consequential claim treated as proven without evidence sufficient to close the decision.

See [SABLE MISPRICING HUNT v1.0](docs/SABLE_MISPRICING_HUNT_v1.0.md).

Run the deterministic gate:

~~~bash
python3 scripts/sable_mispricing_gate.py --file examples/mispricing-hunt-replay-payment.json
~~~

The gate ranks targets but never infers PAID or R3.

## Existing payment commitment gate

The commercial system now gives highest priority to opportunities where the money is already committed and a required closure is still missing.

```text
PAYMENT-COMMITTED
      ↓
UNRESOLVED-OBLIGATION
      ↓
DECISION-BLOCKING
      ↓
CLOSURE-FIT
      ↓
AUTHORIZED
      ↓
PAYMENT-PATH
      ↓
ASSIGNED
      ↓
PAID
```

This is intentionally different from creating a new purchase. The target is an existing contract, paid order, approved budget, acceptance gate, customer delivery obligation, release/settlement condition, or existing payout mechanism with a remaining evidence/verification closure.

Run the gate against an opportunity record:

~~~bash
python3 scripts/sable_payment_commitment_gate.py \
  --file examples/existing-payment-commitment.json
~~~

The gate hard-kills opportunities that cannot establish both an **existing payment commitment** and an **unresolved obligation**. It never infers PAID or R3 from interest, approval, an invoice, a promise, or a payment attempt.

## Why this exists

The practical problem is simple:

A team can claim that a fix worked.
A team can show a green test.
A system can end in the expected state.

None of those necessarily proves that the **history** of the consequential action stayed inside the declared economic or authorization invariant.

SABLE is designed to close that specific UNKNOWN with an independently observed, bounded evidence trail.

## Technical depth

The core implementation is a provider-agnostic **Temporal Economic Integrity Engine**.

It combines:

- economic state machines
- temporal invariants
- idempotency/replay analysis
- authorization boundaries
- event ordering
- reconciliation-aware observation
- adversarial sequence generation
- evidence receipts

The architecture exists to execute a concrete closure.
**The architecture is not the product.**

### v4.2 temporal provenance hardening

SABLE now retains `observed_at_utc` in parsed observations and can reject traces whose timestamps move backward. The new `authorization_effect_binding` invariant checks that observed economic effects are bound to the same declared authorization identity, not merely that an effect happened after some authorization state.

See [`examples/temporal-authorization-binding.json`](examples/temporal-authorization-binding.json) for a complete synthetic trace.


## Public proof + support surface

SABLE now treats every real build as two linked assets:

**Decision Proof** — evidence that closes the buyer's consequential UNKNOWN.

**Builder Proof** — public, inspectable evidence that SABLE itself is being built.

The semantic kernel stays stable:

```text
CLAIM
  ↓
AUTHORIZED BOUNDARY
  ↓
EXECUTION
  ↓
AUTHORITATIVE OBSERVATION
  ↓
INVARIANT
  ↓
VERDICT
  ↓
EVIDENCE
```

The evidence receipt can also carry an explicit **decision context**:

```text
LIVE DECISION
  ↓
DECISION OWNER
  ↓
CRITICAL UNKNOWN
  ↓
CLAIM
  ↓
VERIFIED / NOT_VERIFIED / UNKNOWN
  ↓
DECISION RECORD
```

For a decision-complete run:

```bash
python3 scripts/sable_evidence_gate.py \
  --claim "Replay does not create a second entitlement" \
  --boundary "authorized staging tenant" \
  --action "./run-replay.sh" \
  --verify "./verify-entitlement.sh" \
  --decision-event "release sign-off" \
  --decision-owner "release approver" \
  --critical-unknown "whether replay preserves exactly-one entitlement" \
  --decision-consequence "release may be approved or blocked" \
  --require-decision-context \
  --out sable-evidence-receipt.json
```

Decision context is explicit input, not an inference. SABLE will not invent deadlines, losses, authority, or commercial importance.

### Build in public

When publication is authorized, SABLE can expose real:

- working code;
- technical experiments;
- evidence artifacts;
- research notes;
- failures and corrections;
- measurable milestones;
- source commits.

Synthetic examples remain clearly labeled as synthetic. Private customer data, credentials, secrets, unauthorized traces, fabricated traction, and unsupported claims do not belong in the public surface.

### Support SABLE

SABLE is also discoverable by people who may want to support the project rather than buy a specific closure.

**Who:** an independent builder building SABLE.

**What:** an evidence infrastructure for proving consequential actions actually produced the claimed effect.

**Proof:** public source code, executable gates, receipts, experiments, and documented failures/corrections.

**Why:** keep turning real UNKNOWNs into independently checkable evidence.

**Use of support:** development, compute, hosting, testing infrastructure, and continued public building.

**Support:** [Choose an amount and support SABLE →](https://paypal.me/tang665)

Support is voluntary. A supporter does not become a customer, sponsor, grantor, or investor unless that is the actual relationship.

See [SABLE Public Proof & Capital Surface v1.0](docs/SABLE_PUBLIC_PROOF_AND_CAPITAL_SURFACE_V1.md).

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

---

### Direct purchase

**US$99 — one bounded micro closure:**  
https://paypal.me/tang665/99USD

**US$299 — one bounded decision closure:**  
https://paypal.me/tang665/299USD

Payment is the start condition for an agreed paid scope.

### Important boundary

SABLE only executes work that is explicitly authorized and bounded. No production mutation or unrelated testing is implied by the existence of this repository.

## Unified operating system

SABLE operates as one commercial system with four functions plus one cross-cutting Alliance Leverage Layer — not five threads and not five businesses.

1. **T1 — CASH / R3 HUNTER:** find the next payment-ready buyer, payer and payment path.
2. **T2 — PROOF / PRODUCT ENGINE:** turn the buyer's concrete UNKNOWN into a bounded, fixed-price proof.
3. **T3 — AI SUPER-INDIVIDUAL / CONTEXT ENGINE:** compound commercial memory, evidence, rejected targets and reusable capability.
4. **T4 — REALITY / ANTI-SELF-DECEPTION CONTROL:** veto unsupported commercial states and enforce R3 truth.

The current commercial branches are:

- **Branch 1 — Decision Closure**
- **Branch 2 — AI Buyer Readiness**

The cross-cutting **Alliance Leverage Layer** increases trusted access to current economic events, buyers, payers, decision owners, and lawful evidence boundaries. It is not a separate product or sales pipeline.

Alliance priority:
**A2 Introducer → A3 Economic Gate → A4 Payment Bridge**

Alliance value is measured by movement toward:
**buyer access → payer access → payable-now → settled funds**

See [SABLE Alliance Leverage Layer — Hard Override v1.0](docs/SABLE_ALLIANCE_LEVERAGE_LAYER_HARD_OVERRIDE_V1.md).

Both branches share the same proof kernel and the same R3 gate.

See [SABLE Four-Thread Execution OS v1.0](docs/SABLE_FOUR_THREAD_EXECUTION_OS_V1.md) and [SABLE AI Buyer Readiness v1.0](docs/SABLE_AI_BUYER_READINESS_V1.md).

The operating loop is:

**T1 ↔ Alliance → T2 → T3 → T4 → shared ledger → T1**

Alliance may enter or accelerate any point in the loop but cannot bypass T4 or the R3 gate.

This is a loop, not four independent pipelines.

When the next R3 does not yet exist, resource priority is:

**CASH → PROOF → REALITY CONTROL → CONTEXT COMPOUNDING**

R3 remains the only commercial truth:

**stranger buyer + lawful/authorized transaction + actual settled funds received + verifiable payment evidence**