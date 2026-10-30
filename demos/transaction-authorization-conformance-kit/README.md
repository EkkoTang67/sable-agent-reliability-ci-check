# Transaction Authorization Conformance Kit (local demo)

A small, dependency-free reference harness for one narrow question:

> Does an approval authorize this exact actor, operation, resource, and parameter set — once, and only before expiry?

This repository demo is intentionally local-only. It uses synthetic invoice/payment data and a sandbox executor. It does not connect to an MCP server, ERP, bank, email inbox, payment network, or customer environment.

## Run it

Requires Python 3.10+ and only the Python standard library.

~~~bash
python3 -m unittest -v test_authorization_harness.py
python3 run_demo.py
~~~

The demo shows three outcomes:

1. Changing the approved beneficiary is denied as SCOPE_MISMATCH.
2. The exact approved operation is accepted and sent to a local sandbox executor.
3. Replaying the same approval is denied as APPROVAL_ALREADY_CONSUMED.

The tests also cover actor mismatch, expired approvals, 12 concurrent attempts against one approval, token hashing at rest, append-only audit rows, audit-chain verification, and executor failure.

## What is bound to an approval

The harness hashes canonical JSON containing:

- actor ID;
- operation name;
- resource ID;
- complete parameter object.

An approval also carries a policy version, approver label, issue time, expiry time, and a random bearer token. Only the token hash is stored in SQLite. The token is returned once to the caller.

BEGIN IMMEDIATE and a conditional state transition (APPROVED to CONSUMED) serialize competing uses against one local SQLite database. A successful authorization consumes the approval before the sandbox executor is invoked. Wrong actor or changed parameters are denied without consuming the valid approval, allowing the intended exact action to be retried.

Audit events are append-only through SQLite triggers and linked by a SHA-256 hash chain. This is tamper-evident within this demo, not a signed, externally anchored, or administrator-proof audit log.

## Security and deployment boundaries

This is a reference demonstration, not a production security product or certification.

- The demo does not authenticate the human approver or prove that approved_by has authority. Production approval issuance must sit behind a trusted identity and policy system.
- The SQLite coordination applies to one local database instance. It is not a distributed lock, multi-region consistency mechanism, or high-availability architecture.
- Consuming approval and calling a remote tool cannot be one atomic transaction. A crash between those steps can leave the action outcome unknown. Production adapters need a downstream idempotency key, durable execution state, and reconciliation; this demo does not claim exactly-once external execution.
- The sandbox executor is an in-process function. No real payment, account change, vendor update, or third-party action is performed.
- The token is a bearer credential. A production deployment needs secure transport, secret handling, revocation, retention, rate limiting, and identity binding appropriate to its threat model.
- No customer data or production credentials are included.

## Buyer-validation hypothesis

The intended audience is an implementation partner that repeatedly ships MCP/AI-agent workflows connected to consequential business tools. The commercial question is not whether authorization matters in general. It is whether the partner repeatedly has to prove parameter-bound approval, expiry, replay resistance, and concurrency behavior during client acceptance — and whether it has a budget to buy a reusable acceptance module rather than implementing these tests internally.

This demo is a conversation artifact only. No buyer demand, procurement route, or willingness to pay is established by the code or test results.
