# SABLE Evidence-Bundle Acceptance Matrix v1.0

**Status:** Test specification for sandbox/local validation. Not a production certification, customer result, or proof of revenue.  
**Scope:** Signed receipt, request binding, raw response integrity, payment settlement, identity binding, and conservative aggregate verdicts.  
**Safety:** No live payment, no wallet creation, no production write, no deployment, no credential collection.

## Verdict precedence

- **NOT_VERIFIED** when trusted/authoritative evidence contradicts a required claim (for example, bad signature, wrong request binding, wrong payee/asset/amount, failed transaction, or known signer/payee mismatch).
- **UNKNOWN** when evidence needed to decide is absent, stale, unreachable, or not authoritative enough.
- **VERIFIED** only when every required predicate for the exact bounded claim is present, valid, and consistent.
- A valid signature proves a signature claim, not that a payment settled.
- A successful chain transaction proves only the specific observed transaction/transfer facts; it does not prove the requested URL, response bytes, authorization, identity, or delivery unless those predicates are independently bound and checked.
- Preserve component-level results. Do not hide a known contradiction behind another component's UNKNOWN result.

## Required acceptance matrix

| ID | Fixture / perturbation | Expected component outcome | Expected aggregate outcome | Why |
|---|---|---|---|---|
| EB-01 | Fully synthetic valid receipt; all required predicates explicitly supplied by deterministic fixtures | Signature, request, response bytes, settlement fixture, identity all match | VERIFIED | Positive control only; never label as a real payment |
| EB-02 | Change one byte in the raw response body but keep the receipt digest unchanged | Response integrity NOT_VERIFIED | NOT_VERIFIED | Detect post-issuance payload drift/tampering |
| EB-03 | Supply a different expected request URL or method | Request binding NOT_VERIFIED | NOT_VERIFIED | A receipt must be bound to the exact request being checked |
| EB-04 | Alter a signed receipt field without a valid replacement signature | Signature NOT_VERIFIED | NOT_VERIFIED | Detect receipt tampering |
| EB-05 | Chain evidence shows wrong payee, token contract, chain ID, or amount | Settlement/identity predicate NOT_VERIFIED | NOT_VERIFIED | A successful transaction is not enough if the transfer is the wrong one |
| EB-06 | Authoritative chain receipt says the transaction failed | Settlement NOT_VERIFIED | NOT_VERIFIED | Failure must not be converted into a successful payment claim |
| EB-07 | Chain RPC unavailable, transaction not found yet, or receipt not final enough under the declared policy | Settlement UNKNOWN | UNKNOWN unless another required predicate is already contradicted | Missing observations are not proof of either success or failure |
| EB-08 | Signature and exact transfer checks pass, but original response bytes are unavailable | Those checked components may be VERIFIED; response integrity UNKNOWN | UNKNOWN | Settlement alone cannot prove delivery integrity |
| EB-09 | Signature recovers a signer that differs from the claimed payment payee | Identity binding NOT_VERIFIED; settlement may separately pass | NOT_VERIFIED | A known identity contradiction is decisive |
| EB-10 | Signed receipt says Success, but no independent rail/settlement evidence exists | Signature may be VERIFIED; settlement UNKNOWN | UNKNOWN | Self-declared status is not settlement evidence |
| EB-11 | Required authorization evidence is absent | Authorization UNKNOWN | UNKNOWN | Absence does not prove authorization was granted |
| EB-12 | Authorization evidence exists but its signature, scope, expiry, amount, or recipient contradicts the action | Authorization NOT_VERIFIED | NOT_VERIFIED | An observed violation is not merely missing data |
| EB-13 | Public historical vector: signature and historical transfer may be checked, but vector signer does not equal payment payee and exact original response bytes/request URL are unavailable | Preserve per-component result; identity NOT_VERIFIED; missing delivery predicates UNKNOWN | NOT_VERIFIED, with gaps explicitly reported | Conformance vectors are not production-seller or full-delivery proof |
| EB-14 | Replace all network calls with deterministic fixtures in the ordinary self-test | Test output explicitly says synthetic; no RPC/payment call | Test must pass only as a synthetic test | Keep offline tests deterministic and safe |
| EB-15 | Invoke the read-only live-vector route | It may query only the published historical transaction via read-only chain RPC; it must not call a paid endpoint or submit a transaction | Must report payment_submitted=false and paid_endpoint_called=false, with component details | Live observation is not user revenue and not a customer result |

## Test hygiene

1. Keep deterministic no-network tests separate from read-only historical chain checks.
2. Never use VERIFIED for a full delivery claim if raw response bytes, exact request binding, identity, or any other required predicate is missing.
3. Test both missing evidence and contradictory evidence; they must not collapse into one outcome.
4. Record the code commit, test command, output, time, and environment for every run.
5. Keep actual pull-request state separate from independent test results. Passing tests do not authorize merging.
6. Do not claim Windows compatibility until it has actually been tested on Windows.

## Current known boundary

The repository's synthetic self-test previously passed on the deployed preview for the version identified in the project log. The live-vector route was subsequently added to the sandbox branch but has not yet been deployed or runtime-tested because the Vercel free daily deployment quota was exhausted. Do not describe the new route as verified until an actual run and response have been inspected.

## Next execution sequence

1. Run the no-network test suite locally and confirm EB-01 through EB-06 and EB-10 through EB-14.
2. Add or correct deterministic cases for any missing scenario; record the exact commands and output.
3. After deployment quota resets, deploy only the intended sandbox branch and call the read-only live-vector endpoint once.
4. Inspect component-level and aggregate results. Any mismatch or unexpected VERIFIED is a stop condition.
5. Only after the evidence package is technically sound, evaluate real buyer relevance. Technical correctness alone does not establish demand, a payer, or revenue.
