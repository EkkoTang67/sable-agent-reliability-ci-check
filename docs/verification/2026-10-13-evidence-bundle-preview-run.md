# Independent Verification Record — 2026-10-13

**Purpose:** Preserve independent test observations separately from pull-request and deployment state.  
**Source commit under test:** `009f716c320b6e2b35d06ce6e2a106d16734b7fc` (`test: expand no-payment evidence bundle cases`).  
**Vercel deployment:** `dpl_5KXu29MNNQ8d49GGhCHhYrBaD1gD`, state reported as `READY`, preview URL: https://sable-x402-checkout-preview-qnzv512z5-1164752614-9151.vercel.app  
**Observed at:** 2026-10-13 08:31 UTC (HTTP response Date header).  
**Method:** Read-only HTTP GETs through the authenticated preview-fetch flow. No payment was submitted, no paid endpoint was called, and no production mutation was performed.

## Run A — No-payment synthetic self-test

Endpoint: `GET /api/evidence_bundle_self_test`  
HTTP result: `200 OK`  
Response fields: `test_mode=true`, `synthetic=true`, `payment_required=false`, `payment_submitted=false`, `chain_rpc_called=false`, overall `passed=true`.

| # | Case | Expected | Observed | Result |
|---|---|---|---|---|
| 1 | Fully synthetic valid EIP-712 signature, exact body, exact request, matching settlement fixture | VERIFIED | VERIFIED | PASS |
| 2 | Upstream public x402-receipts signature vector (signature only) | VERIFIED | VERIFIED | PASS |
| 3 | Tampered raw response bytes | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 4 | Wrong expected request URL | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 5 | Wrong expected transaction hash | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 6 | Tampered EIP-712 signature | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 7 | Chain transfer amount differs from signed receipt | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 8 | Chain transaction status is reverted | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 9 | Matching transfer has one confirmation | UNKNOWN | UNKNOWN | PASS |
| 10 | Valid signature recovers to a signer different from `payment.payee` | NOT_VERIFIED | NOT_VERIFIED | PASS |
| 11 | Chain evidence unavailable | UNKNOWN | UNKNOWN | PASS |

**Run A conclusion:** The deployed synthetic test endpoint returned 11/11 cases matching their programmed expected verdicts. The “settlement” used by Run A is an in-memory synthetic fixture, not a real chain lookup and not a customer payment.

## Run B — Read-only historical public chain vector

Endpoint: `GET /api/evidence_bundle_live_vector_test`  
HTTP result: `200 OK`  
Response explicitly reported `payment_required=false`, `payment_submitted=false`, `paid_endpoint_called=false`, `chain_rpc_called=true`.

Historical transaction:
`0xdeb5872c039a88ae37b66ae490c0c8da9b6a4c652d84494ddcc9a05211d6cc80`

| Component | Observed verdict | Interpretation |
|---|---|---|
| Seller EIP-712 signature | VERIFIED | The signature recovers to the known vector-only signer used for conformance testing |
| Historical Base USDC transfer | VERIFIED | The read-only Base RPC evidence matched transaction success, chain, USDC contract, payer, payee, exact atomic amount `5000` (= 0.005 USDC), with 4,038,220 confirmations reported at the time |
| Signer matches claimed `payment.payee` | NOT_VERIFIED | The vector-only signer differs from the `payment.payee` field |
| Exact original response bytes | UNKNOWN | The vector contains a body digest but not the original raw response bytes |
| Exact request URL binding | UNKNOWN | The vector contains hashes, but this test did not establish the exact historical URL with sufficient confidence |
| Full evidence bundle | NOT_VERIFIED | A known identity mismatch is decisive even though the signature and historical transfer components pass |

Transaction reference: https://base.blockscout.com/tx/0xdeb5872c039a88ae37b66ae490c0c8da9b6a4c652d84494ddcc9a05211d6cc80

**Run B conclusion:** The fail-closed aggregate behavior is correct for this public vector: partial component success does not turn an incomplete/mismatched delivery bundle into VERIFIED. This is a historical third-party transaction, not SABLE income, not a customer result, and not evidence that SABLE has any paying customer.

## Important limitations

1. These results describe exactly the two HTTP responses observed at the timestamp above. They do not establish that all code paths, platforms, or production deployments are correct.
2. The self-test checks verifier logic using synthetic in-memory data; it cannot replace a real authorized buyer transaction or acceptance test.
3. The read-only historical vector cannot prove the original service delivery because the exact response bytes and exact request URL are unavailable.
4. The current endpoint does not yet independently evaluate an authorization/mandate object. Authorization-specific acceptance cases remain future requirements, not verified current capability.
5. Independent test outcome and GitHub PR state are separate. Passing tests do not authorize merging.
6. **Commercial ledger unchanged:** R3 = 0. No stranger-buyer payment to a user-controlled account was observed in these tests.
