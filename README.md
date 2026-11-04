# SABLE — Your system says it worked. We check the real result.

SABLE checks whether a claimed payment, refund, order, entitlement, release, or AI-agent action reached the required real-world state.

**First use case: Payment went through. Did the customer actually get the correct access or delivery?**

A success message is not the same as a proven outcome. SABLE binds one exact claim to authorized evidence from the relevant system of record and returns one of three verdicts:

- **VERIFIED** — the required outcome is supported by the evidence.
- **NOT_VERIFIED** — the evidence contradicts the claim.
- **UNKNOWN** — the evidence is missing, stale, conflicting, or not authoritative enough.

**The technical boundary:** the action system reports; the system of record answers. SABLE produces a bounded, reviewable evidence receipt. It does not claim universal exactly-once execution or production certification.

## Decision Error Correction System

The operating system now includes **DECS v1.0**: a mandatory protocol for catching wrong assumptions early, limiting the cost of being wrong, and preventing repeated decision errors. It requires falsifiable claims, counter-hypotheses, cheapest discriminating tests, pre-set exposure caps, explicit stop conditions, post-test error diagnosis, and reusable corrections.

- [Decision Error Correction System v1.0](docs/decision-quality/DECISION_ERROR_CORRECTION_SYSTEM_V1.md)
- [Decision Record Template](templates/decision-quality/DECISION_RECORD_TEMPLATE.md)
- [Claim Confidence & Evidence Weighting v1.0](docs/decision-quality/CLAIM_CONFIDENCE_AND_EVIDENCE_WEIGHTING_V1.md)

DECS governs decisions across the AI operating system; it complements the existing evidence-weighting and feedback-to-cash controls.

## Adversarial Opportunity & Judgment Engine

**AOJE v1.0** adds an offensive reverse-thinking layer to DECS. It does not merely protect existing plans from failure; it actively searches for neglected bottlenecks, buyer constraints, competitor blind spots, power shifts, and asymmetric openings. Every material candidate is attacked from the anti-customer, competitor, constraint, value-capture, and self-bias perspectives before resources are committed.

- [Adversarial Opportunity & Judgment Engine v1.0](docs/decision-quality/ADVERSARIAL_OPPORTUNITY_JUDGMENT_ENGINE_V1.md)

Operating doctrine: **be aggressive toward uncertainty; be conservative with irreversible exposure.**

## Ekko Strategic Intelligence & Wisdom Integration OS

**Ekko Strategic Intelligence & Wisdom Integration OS v1.0** integrates strategic direction, DECS error correction, AOJE adversarial opportunity discovery, and evidence-led extraction of human knowledge into one operating cycle. It establishes the rule: **fast with direction, fast without chaos, fast without carelessness.**

- [Ekko Strategic Intelligence & Wisdom Integration OS v1.0](docs/strategy/EKKO_STRATEGIC_INTELLIGENCE_WISDOM_INTEGRATION_OS_V1.md)

This is an integration specification and human-reviewable operating doctrine. It is not yet autonomous runtime enforcement, and it does not claim that the 500-book catalog has been deeply absorbed.
