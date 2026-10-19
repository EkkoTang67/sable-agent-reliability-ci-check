# Agent Constraint & Action-Boundary Check — Paid Pilot

**US$99 · one workflow · one critical rule · up to 8 tests · one evidence report**

## The purchase decision

For teams building or shipping tool-using AI agents, the question is not only whether the model can repeat an instruction. It is whether a critical constraint is still respected when the agent reaches a later turn and a tool could create an external side effect.

Examples of the constraint being tested:
- Do not send an email or message unless this task has explicit authorization.
- A stop/park decision must not be reopened by stale context.
- A tool call must not execute when approval is missing.
- A prior approval must not authorize a different action, destination, or payload.

This is an **independent, bounded regression check**, not a new runtime security gateway.

## Fixed pilot scope — US$99

For one agent workflow and one written critical rule, the pilot includes:

1. Up to 8 test scenarios, including relevant follow-up-turn and stale-context cases.
2. A test matrix with the expected behavior and observable evidence required for each case.
3. A bounded execution or review using an authorized sandbox, mocked side-effect tools, or appropriately sanitized traces supplied by the buyer.
4. A machine-readable result bundle and a concise report with **PASS / FAIL / UNKNOWN** per case, evidence references, reproduction notes, and limitations.

Target delivery: within 2 business days **after** scope fit and required test inputs are confirmed. If the agent cannot be tested with the supplied interface or evidence, that limitation is stated instead of inventing a PASS.

## Buyer fit

Best fit: a developer or implementation team with an existing tool-using agent that is approaching a customer acceptance test, release, or deployment decision.

Before payment, send only:
- the agent framework/model family and approximate version;
- the one constraint that must not be violated;
- whether an authorized sandbox, mocked tool harness, or sanitized execution traces are available.

No meeting is required. Do not send credentials, customer data, private prompts, secrets, or production access. If the requested scope cannot be tested safely, no payment is requested.

## Acceptance boundary

The deliverable is accepted when the agreed scenario set has a result for each case, every PASS/FAIL is linked to the observed evidence, and blocked or missing evidence is marked UNKNOWN. The service does **not** promise that every failure in the agent has been found, guarantee safe behavior in all contexts, or certify the system for production.

No production mutation, real message send, real payment, or unapproved external action is part of this pilot. Any tool capable of side effects must be mocked or run in a buyer-authorized sandbox.

## Price and payment

**Fixed price: US$99 once. No subscription. No automatic renewal.**

[Pay US$99 via PayPal](https://paypal.me/tang665/99USD)

Payment note: `PRODUCT=AGENT_BOUNDARY_CHECK`

Payment does not itself grant system access or authorize any action. Scope and the safe test boundary must be confirmed before execution.

## Evidence status

This is a new paid pilot offer. No customer purchase, customer case study, or revenue from this offer is claimed. The first validation target is a real buyer willing to pay for this defined scope.


## Public test matrix

The eight candidate failure-mode tests and evidence required for each are listed in the [Agent Action-Boundary Regression Matrix](AGENT_ACTION_BOUNDARY_TEST_MATRIX_V1.md). It is a test plan, not a test result. Public issue reports inform the test design but are not represented as customer findings or proof of a current vulnerability in every framework/version.
