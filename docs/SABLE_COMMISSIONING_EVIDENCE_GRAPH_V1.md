# SABLE Commissioning Evidence Graph v1.0

## Product boundary

SABLE is a vendor-neutral, read-only evidence relationship layer over commissioning and turnover artifacts. It answers one narrow question:

**Does the supplied package contain a traceable, internally consistent chain from asset and governing revision through test result, deficiency remediation, retest, and required witness evidence?**

It is not a commissioning management system, building automation system, control plane, engineering authority, safety certifier, or substitute for a responsible professional's acceptance decision.

## Graph vocabulary

Supported node kinds: asset, drawing, procedure, test, test_result, deficiency, corrective_action, retest, witness, turnover_package.

Supported directed relations: contains_asset, contains_evidence, tests_asset, uses_drawing, uses_procedure, has_result, evidence_for, corrected_by, retests, follows_result, witnesses (witness record to test result).

Each evidence-bearing node must include a relative local source_ref and declared SHA-256 digest. The validator reads bytes locally and computes the digest. It never follows URLs or network paths. Missing files and incomplete authority metadata result in UNKNOWN; digest mismatch, explicit failed tests, unapproved/outdated governing documents, open deficiencies, unsigned required witness evidence, or reversed retest time result in NOT_VERIFIED.

## Run the synthetic fixture

From the repository root:

~~~bash
python3 sable_commissioning_evidence_graph.py --file examples/commissioning-evidence-graph.synthetic.json --root . --out commissioning-evidence-receipt.json
~~~

The fixture is explicitly synthetic. Its text files are not real commissioning records and must never be presented as project evidence.

## Verdict semantics

- VERIFIED: only the declared v1 graph and local digest gates passed.
- NOT_VERIFIED: supplied evidence contradicts a declared v1 gate or a digest does not match.
- UNKNOWN: necessary linkage, source bytes, timestamps, or authority flags are absent or cannot be established.

Exit codes: 0 = VERIFIED, 1 = NOT_VERIFIED, 2 = UNKNOWN. In release or acceptance CI, treat anything other than VERIFIED as blocking; the responsible operator retains decision authority.

## Integrity and safety boundaries

- Local read-only file access only. No facility network connection.
- No BMS, EPMS, SCADA, PLC, BAS, controller, or equipment command.
- No automated test execution or energization.
- No automatic sign-off, acceptance, or merge authorization.
- A hash match establishes byte identity against the declared digest only; it does not establish authorship, correctness, approval authority, or authenticity of a human signature.
- The v1 prototype does not parse PDF drawings, validate engineering meaning of test values, verify signatures cryptographically, or fetch authoritative records directly from source systems.
- An independent reviewer and qualified commissioning authority must decide whether evidence is sufficient for real acceptance.

## Commercial hypothesis

The initial paid unit is one bounded subsystem turnover/IST evidence package, not a platform rollout. A pilot should be purchased by a commissioning authority, owner's representative, data-center operator, general contractor, or controls integrator with a live acceptance or handover deadline and a documented evidence gap. The buyer must confirm that the gap changes a current acceptance, release, remediation, or turnover decision and that an accountable payer can authorize payment.

A target, interview, email sent, or technically complete prototype is not a sale. SABLE records R3 only after verifiable funds settle in the seller-controlled account.

## Next product gates

1. Run this local fixture and edge cases in CI.
2. Add redacted exports/adapters for one real authorized source system, without write credentials.
3. Calibrate rules against a commissioning professional's independently labelled sample set.
4. Obtain a paid, bounded pilot and permission to process redacted evidence before expanding data formats.
5. Add audit-grade version pinning and signed receipts only after threat modelling and explicit key-management design.
