# Opportunity Swarm v1.0 — 10,000 AI-agent identities, two commercial engines

## Purpose

Build a swarm with **10,000 registered AI-agent identities** split across two economic engines and an independent audit pool:

- **4,500 prototype-to-cash scouts:** find funded, bounded cash tasks and define acceptance checks.
- **4,500 niche-pain scouts:** discover repeated, costly workflow failures and design buyer-verifiable experiments.
- **1,000 commercial auditors:** challenge claims, look for counterevidence, and check payer, budget, costs, competition, eligibility, and settlement.

The executable runtime is `scripts/swarm_runtime.py`. It stores agent identities, task queues, status, results, and event history in SQLite. Each executed task assigns a scout plus a distinct auditor and runs **two model calls** through an OpenAI-compatible endpoint. A scout result is not treated as fact; the audit stage can return HOLD or REJECT.

This is a real, model-backed execution path—not only a static manifest—but it does **not** claim 10,000 simultaneous LLM sessions. The 10,000 identities exist independently of model calls; work is activated through a queue with explicit concurrency and call limits. The default model endpoint is local Ollama. Remote inference is blocked unless the operator passes `--allow-remote`, because remote APIs may incur charges and transmit task data.

## The unit of work: scout + adversarial auditor

- **Scout:** discovers a task or workflow, forms a bounded hypothesis, and proposes a test.
- **Commercial reality auditor:** attempts to disprove the hypothesis, separates evidence from inference, and enumerates unresolved facts.

The auditor is a separate registered agent. A candidate without primary evidence remains unknown. External contacts, security actions, payment operations, and production changes are not performed automatically.

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

- Register 10,000 distinct agent IDs across the two scout lanes and audit pool.
- Cover 50 candidate verticals; distribute agents across the verticals so no single category consumes the whole swarm.
- The registry is idle by default. No LLM call happens during initialization; only explicitly queued tasks use model inference.
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

## Runnable agent system

Requires Python 3.10+; runtime state uses SQLite from the Python standard library. Model inference needs a locally running OpenAI-compatible endpoint or a remote model API. The default endpoint is local Ollama.

### 1. Register 10,000 real agent identities (zero model calls)

```bash
python3 scripts/swarm_runtime.py init --count 10000 --db state/swarm.db
python3 scripts/swarm_runtime.py status --db state/swarm.db
```

Expected registry: 4,500 prototype-cash scouts, 4,500 niche-pain scouts, and 1,000 commercial auditors.

### 2. Discover public issue signals (network call only when explicitly invoked)

```bash
python3 scripts/swarm_runtime.py discover-github \
  --query '"cash bounty" is:issue is:open' \
  --mode prototype_cash --limit 20 --out state/cash-signals.jsonl

python3 scripts/swarm_runtime.py discover-github \
  --query 'manual workaround is:issue is:open' \
  --mode niche_pain --limit 20 --out state/pain-signals.jsonl
```

Public GitHub issue search is a **signal source**, not proof of a live reward, buyer, acceptance, eligibility, or payment. The current adapter imports the issue body and metadata; it does not read the full comment history or independently verify payout terms.

### 3. Queue and run a small number of tasks

```bash
python3 scripts/swarm_runtime.py enqueue --input state/cash-signals.jsonl --db state/swarm.db
python3 scripts/swarm_runtime.py enqueue --input state/pain-signals.jsonl --db state/swarm.db

# Requires a model already installed and running in local Ollama:
# Set this to the exact local model name you installed.
export SWARM_MODEL="YOUR_INSTALLED_MODEL_NAME"
python3 scripts/swarm_runtime.py run --db state/swarm.db \
  --workers 1 --max-tasks 1 --max-llm-calls 2
python3 scripts/swarm_runtime.py status --db state/swarm.db
```

Windows PowerShell equivalent for the model variable:
```powershell
$env:SWARM_MODEL = "YOUR_INSTALLED_MODEL_NAME"
python scripts/swarm_runtime.py run --db state/swarm.db --workers 1 --max-tasks 1 --max-llm-calls 2
```

Each task uses at most two model calls: scout, then independent auditor. The runtime caps output length, defaults to one task at a time, and refuses remote inference unless `--allow-remote` is explicitly supplied. A remote API may be paid; free ChatGPT or DeepSeek web access does **not** itself provide a free API endpoint.

### 4. Regression test

```bash
python3 -m unittest discover -s tests -v
```

The tests cover 10,000 distinct registered IDs, lane distribution, queue de-duplication, two-agent execution, explicit remote-call opt-in, and non-payment claims. They use mocked model responses; they do not prove live model quality or real earnings.

The older `scripts/opportunity_swarm.py` remains a lightweight deterministic screener. The runtime above is the model-backed execution path. Neither script independently proves a source, commits the operator to work, contacts buyers, nor receives money.

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
