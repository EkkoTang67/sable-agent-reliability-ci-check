# Opportunity Swarm v1.0 — 10,000 logical pairs, two commercial engines

## Purpose

Build a swarm of **10,000 logical human–AI work units** that explores two complementary routes:

1. **Prototype → cash:** find an explicit paid task or a buyer with a current purchase trigger; make the smallest deliverable that can pass the stated acceptance test; prove acceptance and settlement.
2. **Niche pain → large upside:** identify a narrow, repeated, expensive failure in a real workflow; identify the payer and existing workaround; seek a buyer action; prototype only after evidence improves.

This is not a claim that 10,000 independent LLMs are running. The first version creates 10,000 dormant slots at zero model-call cost. Work slots activate only when evidence justifies additional cost. Ten thousand slots are inventory and allocation capacity, not ten thousand paid API sessions.

## The unit of work: a pair, not a chatbot

Each pair has two opposing responsibilities:

- **Scout / builder:** discovers a task, workflow, or testable hypothesis; proposes an economical experiment.
- **Commercial reality auditor:** tries to disprove the claim; checks the source, actual payer, budget trigger, acceptance standard, alternatives, competition, eligibility, costs, and settlement path.

The auditor is not allowed to rubber-stamp the scout. A candidate without primary evidence remains unknown.

## Two engines

### Engine A — Prototype-to-cash

Target work already connected to money: funded bounties, scoped paid tasks, paid pilots, or explicit buyer requests.

Minimum record:
- primary source URL and access date
- task status; named payer or funder
- cash amount and currency, not points/airdrop expectations
- exact acceptance criteria
- confirmed zero upfront cost
- payout rail and written eligibility confirmation for a mainland-China individual
- competition / first-merged / review-order constraints
- estimated effort and a strict time cap

Hard gate: a missing fact means HOLD; a positive required deposit or stake means REJECT. A listed amount is not a payment guarantee. A task is not “cash” until the payment settles.

### Engine B — Niche pain to high-value prototype

Look for repeated operational exceptions where the cost is borne by an identifiable organization or role, for example reconciliation exceptions, incorrect entitlements after a payment, supplier-document failures, or release evidence that must be recreated manually.

Minimum record:
- precise user and budget owner (not just “companies”)
- observable trigger and recurrence
- economic consequence: time, rework, delay, loss, compliance exposure, or blocked revenue
- current workaround and why it persists
- primary evidence (public issue, job listing, operator statement, workflow spec, etc.)
- buyer action: shared real sample, introduced budget owner, scheduled scoped trial, budget confirmation, purchase, or paid pilot
- safe data boundary and prototype acceptance test

A painful story alone is not demand. “READY_FOR_PROTOTYPE” requires a meaningful buyer action such as a paid pilot, purchase, budgeted trial, or signed commitment. Other evidence advances only to payer validation.

## State machine

`DETECTED → EVIDENCE_PENDING → QUALIFIED → PROTOTYPE → BUYER_TEST → COMMITTED → SETTLED`

- **DETECTED:** a signal exists; no commercial inference yet.
- **EVIDENCE_PENDING:** source, payer, payment path, or impact remains unverified.
- **QUALIFIED:** the hard gates pass and a bounded test is worth running.
- **PROTOTYPE:** the smallest deliverable exists and can be checked.
- **BUYER_TEST:** a real target user has tried or assessed it against explicit criteria.
- **COMMITTED:** an authorized buyer commits money or a formally defined funded reward.
- **SETTLED:** the payment has arrived in the user-controlled account and the evidence is recorded.

A reply, star, install, demo request, PR submission, merged code without payment, invoice, approval, or pending transfer is not SETTLED.

## Scale without burning money

- Generate 10,000 logical slots, balanced 50/50 between the two engines.
- Cover 50 candidate verticals initially; distribute slots across the verticals so no single category consumes the whole swarm.
- Keep every slot dormant by default. Do not call an LLM just because a slot exists.
- Use deterministic filters and cached evidence first; use free/manual research next; invoke model-assisted work only for candidates that pass a gate.
- Keep a human approval gate for contacting third parties, running code, using customer data, signing agreements, spending money, and submitting work.
- Do not automate account creation, fake identities, spam, unauthorized security testing, or circumvention of eligibility/region rules.
- Enforce per-candidate time, tool-call, and spending budgets. v1 cash budget is zero.

## Ranking and hard rejection

Rank candidates using **evidence strength, economic consequence, recurrence, payer clarity, buyer access, solution feasibility, competition, and settlement confidence**. Do not rank on hype, market size claims, token points, or headline bounty amounts alone.

Immediately reject:
- upfront deposits, paid access, required staking, or unapproved spend
- task closed, already solved, or blocked by a clearly earlier accepted claim
- crypto-only payment when it fails the user's eligibility/legal/payment constraints
- work requiring unauthorized access, production side effects, or data the operator is not authorized to use
- unverifiable rewards, vague acceptance rules, or claims that rely on fabricated evidence

Hold—not pass—when funding, payment route, eligibility, scope, or cost is unknown.

## Runnable zero-cost prototype

Requires Python 3.10+; no dependencies and no network calls.

Generate the 10,000 logical slots:

```bash
python3 scripts/opportunity_swarm.py seed --count 10000 --out swarm-manifest.jsonl
```

Screen candidates from a JSONL file:

```bash
python3 scripts/opportunity_swarm.py screen \
  --input examples/opportunity-candidates.sample.jsonl \
  --out screened-candidates.jsonl
```

Run regression checks:

```bash
python3 scripts/test_opportunity_swarm.py
```

The sample candidates are intentionally synthetic. The script only checks supplied evidence; it does not independently verify URLs, find live jobs, execute code, contact buyers, or receive money.

## Success metrics

The first stage does not measure number of agents, prompts, or pages scraped. Track:
- qualified candidates per 100 signals
- time to reject a bad opportunity
- verified payer / payment-path rate
- buyer actions per prototype
- paid conversion rate
- time from first evidence to settled money
- repeat purchase / second transaction rate
- cost per qualified candidate and per settled transaction

First proof target: one end-to-end transaction with a stranger buyer and actual settled funds. Only then expand active model calls and parallelism.
