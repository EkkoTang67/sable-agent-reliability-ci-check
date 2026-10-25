# Stripe Billing Failure-Path Preflight — US$99 Pilot

**One Stripe billing workflow. One bounded check. An evidence-backed decision before launch.**

A successful checkout page does not prove every downstream billing effect happened correctly. This pilot focuses on one high-risk path: a payment, subscription, or credit-balance event reaches the application, and the application must grant/revoke the intended access or balance change once—and only once.

## Who this is for

A solo founder or small SaaS team that:
- uses Stripe Checkout, subscriptions, or credit-based billing;
- is preparing a launch, adding paid access, or investigating a billing/webhook issue; and
- can authorize a narrow review of the relevant code and test evidence.

The strongest fit is a concrete decision with a deadline: “Can we launch this billing path before we send traffic?” or “Why did credits/access drift after a payment event?”

## Fixed scope — US$99

One workflow, one webhook handler, and up to three relevant source files plus related tests/schema supplied by the buyer.

The review checks the applicable items below:
1. Signature verification uses the exact raw request body and enforces the provider’s timestamp window.
2. Repeated delivery of the same event does not repeat the business side effect.
3. Separate events for the same payment/business object cannot grant duplicate credits or fulfillment.
4. Failure responses, retries, and durable event recording do not silently lose or repeat a state change.
5. Payment status is not confused with entitlement state, fulfillment, or bank payout settlement.
6. Stale/out-of-order subscription events do not overwrite a newer state without an explicit reconciliation rule.

The report does not mark a case PASS merely because code looks plausible. Each result is tagged **VERIFIED / NOT_VERIFIED / UNKNOWN / DISPROVEN / PARKED**, with the relevant evidence and limitations.

## Deliverable and timing

- A concise findings report and evidence matrix.
- Reproduction notes for checks actually run.
- Prioritized issues and a testable acceptance criterion for each recommendation.
- Target delivery within 2 business days after scope fit, inputs, and the safe test boundary are confirmed.

The test matrix is limited to the agreed workflow. It is not a full security audit, compliance certification, penetration test, or guarantee that every bug has been found.

## Safe boundary

- Review only code the buyer is authorized to share.
- Use sanitized excerpts, mocked side-effect tools, or buyer-authorized Test mode.
- Do not send live API keys, production secrets, customer personal data, or private payment details in chat or payment notes.
- No live-mode payment, capture, refund, production deployment, or production write is included.
- If necessary evidence cannot be obtained safely, the result stays UNKNOWN rather than being guessed.

## Price and payment

**Fixed price: US$99 once. No subscription or automatic renewal.**

[Pay US$99 via PayPal](https://paypal.me/tang665/99USD)

Payment note: `PRODUCT=MICRO_CLOSURE` + `STRIPE_FAILURE_PATH_PREFLIGHT`.

Before paying, a buyer may first send only the workflow, the decision/deadline, and what sanitized code/test boundary is available to [confirm scope fit](mailto:sable-verification@agentmail.to?subject=Stripe%20billing%20failure-path%20scope%20fit&body=WORKFLOW%3A%20%0ADECISION%20%2F%20DEADLINE%3A%20%0AAUTHORIZED%20TEST%20BOUNDARY%3A%20%0A). No call is required. Scope and authority must be confirmed before execution; payment does not itself authorize system access.

## What has already been tested

The related lab currently has 33 passing local Python tests. Separate Stripe Test mode work observed:
- same-key/same-parameter PaymentIntent replay returning the same object, and same-key/different-parameter reuse rejected;
- an actual Stripe CLI-forwarded webhook event whose raw-body HMAC-SHA256 signature validated; and
- replay of the identical signed event being handled as a duplicate by the local receiver.

These are controlled lab observations—not a customer case study, not an audit of your application, not a production safety guarantee, and not proof of bank settlement. The PaymentIntent and webhook observations came from different Stripe test accounts.

## Acceptance criteria

The deliverable is accepted when the agreed cases have explicit results; every material PASS/FAIL has evidence references; any missing access or unrun test is labeled UNKNOWN/NOT_VERIFIED; and each recommended fix has a testable acceptance criterion.

**No customer purchase or revenue from this pilot is claimed yet.** The commercial test is whether a qualified buyer with a real deadline will pay for this defined scope.
