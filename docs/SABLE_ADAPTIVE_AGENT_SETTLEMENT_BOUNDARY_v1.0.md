# SABLE ADAPTIVE AGENT SETTLEMENT BOUNDARY v1.0
## Research/design note — sandbox only, not a production guarantee

Date: 2026-10-13
Status: Research hypothesis; implementation and buyer demand not yet verified.

## 1. Terminology: avoid ambiguity

“Adaptive technology” has multiple meanings. In accessibility, “adaptive technology” commonly refers to tools that help people with disabilities use devices or complete tasks. This document uses **adaptive agent system** in a narrower software sense: an agent whose plan or behavior changes when context, observations, or goals change.

Sources:
- Canadian government terminology database, adaptive technology: https://www.btb.termiumplus.gc.ca/tpv2alpha/alphafra.html?__index=alt&i=1&index=alt&lang=eng&srchtxt=ADAPTIVE+TECHNOLOGY
- Adaptive software systems literature (situational adaptation): https://www.sciencedirect.com/science/article/pii/S0950584904000722

Do not rebrand SABLE as an “adaptive technology” product until the specific meaning in the referenced video or market context is confirmed.

## 2. Strategic hypothesis

The useful boundary is not “make the agent adapt better.” It is:

**Let an adaptive agent reason about uncertain conditions, but do not let its own changing belief count as proof that an irreversible external action succeeded.**

A 2026 IMF note on agentic payments describes the structural tension between probabilistic agents and deterministic payment infrastructure, warning about adaptive systems making irreversible payments without adequate controls, checks, and accountability:
https://www.elibrary.imf.org/view/journals/068/2026/004/article-A001-en.xml

Google's AP2 positions signed mandates as evidence of user intent and transaction accountability:
https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol

This does **not** prove a market gap exists for SABLE. It motivates a testable hypothesis: in some integrations, authorization evidence and a seller-issued “Success” receipt may still need separate, independently checked evidence of execution, delivery, and settlement.

## 3. Proposed boundary model

1. **Adaptive decision layer** — observes conditions, selects/revises a plan, and explains the intended action. Its output is a proposal, not proof of execution.
2. **Authorization/policy layer** — checks actor identity, signed mandate, scope, expiry, amount/recipient constraints, and required human approval. Missing or invalid authorization blocks execution.
3. **Execution layer** — the payment rail or external service carries out the operation. SABLE does not execute payments or mutate the external system.
4. **Independent evidence layer (SABLE target)** — correlates the original authorized request, the signed receipt, exact response bytes where relevant, and independently observed terminal transaction state.
5. **Decision layer** — emits VERIFIED, NOT_VERIFIED, or UNKNOWN for a specific claim. The downstream caller chooses its own fail-safe action.

The key separation is:
- authorization proves what was permitted;
- a receipt/signature proves what a trusted signer asserted;
- raw-byte binding proves which response bytes match a commitment;
- independent rail evidence supports whether a payment settled;
- none of these claims implies all the others.

## 4. Fail-closed verdict semantics

### VERIFIED
Return only when all required predicates for the requested claim are evidenced and consistent. For a paid-delivery claim this normally requires:
- trusted signer verification;
- signed receipt fields bound to the expected request and operation;
- exact response bytes match the receipt's body digest;
- correct chain/rail, transaction identity, terminal success, asset, payer, payee, and atomic amount;
- sufficient independent confirmation/finality for the supported rail;
- no known mismatch between receipt signer, authorized seller, and payment recipient.

### NOT_VERIFIED
Return when available evidence positively contradicts a required predicate: invalid signature, tampered response, wrong request/transaction, wrong payer/payee/asset/amount, failed/reverted transaction, or known signer/recipient mismatch.

### UNKNOWN
Return when a required fact cannot be established: missing raw response bytes, missing/failed RPC, unsupported network, missing authorization artifact, or unavailable finality evidence. Do not downgrade a known contradiction to UNKNOWN just because other evidence is missing.

A self-declared Boolean such as `rail_confirmation_verified=true`, a status string `Success`, a UUID, or a signed receipt alone is not independent settlement evidence.

## 5. Minimum no-payment test matrix

- Valid synthetic signature + exact raw body + exact request + matching mocked settlement -> VERIFIED (synthetic only).
- Public known EIP-712 fixture -> signature compatibility checked against explicitly named vector signer; never assume vector signer is the real payee.
- Body tampered -> NOT_VERIFIED.
- Request URL/method/params mismatch -> NOT_VERIFIED.
- Transaction hash or transfer recipient/amount/asset mismatch -> NOT_VERIFIED.
- Known signer-to-payee mismatch -> NOT_VERIFIED for the identity/paid-delivery claim, even if the historical transfer itself succeeded.
- Chain evidence unavailable but no known contradiction -> UNKNOWN.
- Missing raw body -> UNKNOWN for byte-for-byte delivery.
- Every test labels whether chain evidence is synthetic or independently observed.

Passing these tests validates a verifier implementation, not a customer transaction, product-market fit, or revenue.

## 6. Boundary / safety rules

- Read-only auditor by default; do not submit payments, retry orders, refund, release funds, or change production state.
- Keep original PR/deployment state separate from independent test results.
- No merge or release authorization from passing tests alone.
- Never use a historical third-party payment as SABLE revenue.
- Preserve provenance: synthetic evidence, public explorer/RPC evidence, seller-provided artifacts, and buyer-provided artifacts must be distinguished.
- Prefer a narrow adapter/API/CLI that can plug into existing agent/payment systems over building a new adaptive agent or new payment protocol.

## 7. Strategic optionality — “win without a resource war”

Compare the real alternatives for each observed workflow:
A. use existing protocol/library as-is;
B. add a local integration check;
C. adopt SABLE as an independent evidence gate;
D. build the capability internally;
E. partner/license/acquire an asset.

Do not presume C, D, or E is best. SABLE has strategic value only if it proves an important property that an existing implementation does not cheaply and adequately provide, and if independent users can adopt it with low friction.

Potential moat is not secrecy of a short verifier script. It would have to accumulate from compatible adapters, independently reproducible test vectors, trusted evidence provenance, integration adoption, and documented reductions in real decision risk.

## 8. Next action and go/no-go criteria

Next action: when the deployment quota is available, run the read-only live-vector route from the sandbox branch. Validate its chain observation independently; the public vector's test-only signer mismatch and absent original response body must keep the overall paid-delivery claim NOT_VERIFIED/UNKNOWN according to the exact predicates.

Then find one real authorized workflow where the owner can provide the signed authorization, receipt, original response bytes, transaction identifier, and expected settlement facts. Do not contact anyone or claim buyer interest without explicit user authorization.

Go only if:
- a third party can reproduce the verdict from supplied evidence;
- positive and negative cases separate correctly;
- the integration is materially easier than bespoke checking;
- an owner has a real decision and measurable consequence;
- payer, legal route, price/budget, and settlement path are confirmed before any R3 claim.

Stop or pivot if existing protocol/tooling already delivers the needed assurance at lower cost, no real workflow needs the check, or critical evidence cannot lawfully be collected.

## 9. Facts / inference / unknown ledger

**FACT**
- Existing SABLE sandbox synthetic self-test passed 6 tests at deployment commit `a139e075`.
- Public Blockscout results showed the published historical transaction `0xdeb5872c039a88ae37b66ae490c0c8da9b6a4c652d84494ddcc9a05211d6cc80` as successful with a matching 5,000-unit USDC transfer; this was not a SABLE payment.
- New read-only route source is on the sandbox branch but the daily Vercel deployment quota was exhausted on 2026-10-13, so that route was not deployed or executed.

**INFERENCE**
- Separating adaptive decision-making from deterministic execution evidence may be useful in some agentic payment workflows.
- A compact independent evidence gate may be easier to adopt than a new payment protocol.

**UNKNOWN**
- Whether a named external team has this problem in a production workflow.
- Whether an independent gate provides value beyond its existing provider/protocol and monitoring.
- Whether anyone will pay for it, at what price, and through which compliant payment route.
- Whether this creates any acquisition interest.

R3: 0.