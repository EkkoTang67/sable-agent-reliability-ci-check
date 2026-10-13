# SABLE x402 Execution-Evidence Verifier (Experimental)

This adapter verifies the open `x402ev/1` execution-evidence proposal described in
[x402-foundation/x402 PR #3682](https://github.com/x402-foundation/x402/pull/3682).
The proposal is not treated here as a finalized standard.

## What VERIFIED means

The command returns `VERIFIED` only when:
1. The receipt's RFC 8785 JCS canonical body produces the declared `evidenceRef`.
2. The receipt carries an Ed25519 signature valid for that canonical body.
3. The receipt signer public key matches an externally pinned key supplied by the caller.
4. The raw response-body bytes match the signed `delivery.contentDigest`.
5. The receipt binds the expected transaction hash, CAIP-2 network, payee, token contract, atomic amount, and a successful HTTP 2xx status.

The verifier deliberately does not claim semantic correctness, genuine compute execution, independent witnessing, settlement finality, or an authorized downstream state transition. Those are separate checks.

## Inputs

- `--receipt-json`: JSON containing the `execution-evidence.info` object, the full `execution-evidence` extension object, or the `info` object itself.
- `--body-file`: exact response-body bytes as received by the client. Do not reserialize JSON before hashing.
- `--trusted-public-key`: base64url Ed25519 public key obtained from an external trust source, such as DNS, PKI, or a pinned registry. Do not trust the key merely because the receipt declares it.
- `--expected-tx`, `--network`, `--payee`, `--amount`, `--asset`: payment fields independently expected by the caller.

## Example invocation

```bash
python scripts/sable_x402_execution_evidence.py \
  --receipt-json execution-evidence.json \
  --body-file response-body.bin \
  --trusted-public-key '<externally-pinned-base64url-public-key>' \
  --expected-tx 0x... \
  --network eip155:8453 \
  --payee 0x... \
  --amount 0.05 \
  --asset 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913 \
  --asset-decimals 6
```

Exit codes: `0` = signed content-binding verified; `1` = NOT_VERIFIED; `3` = UNKNOWN; `2` = CLI input could not be loaded.

A missing/unauthenticated trust key must remain `UNKNOWN`. A body-digest mismatch, invalid signature, key mismatch, or contradictory payment field is `NOT_VERIFIED`. The main SABLE settlement audit must still verify actual on-chain finality separately.
