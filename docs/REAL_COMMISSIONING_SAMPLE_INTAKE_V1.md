# SABLE — First Authorized Commissioning Sample Intake v1.0

## Purpose

Validate the evidence graph against one real, authorized, redacted commissioning/turnover sample before building a source-system adapter. This is a bounded software evaluation, not engineering acceptance or safety assurance.

## Request

One historically completed subsystem package with approximately 8–15 redacted UTF-8 text sidecars plus one JSON graph manifest, ideally including one known, already-adjudicated documentation gap or mismatch. The data owner must have authority to share the sample for this evaluation and must expressly approve the use.

Preferred starting scope: a non-sensitive subsystem such as a cooling skid, an AHU, or a non-live lab/commissioning package. The sample must not contain live controls access or instructions to operate equipment.

## Supported intake format in v1

The executable v1 directly reads a JSON graph manifest plus local UTF-8 text sidecars whose key/value fields are explicitly mapped in the graph. It does not directly ingest raw CSV/JSON exports, binary PDFs, native CAD files, vendor portals, or engineering drawings. A source CSV/JSON may be considered only if the authorized data owner and SABLE agree a manual, documented redacted-field normalization step; no automatic parser or platform adapter is implied. Do not upload sensitive originals in order to test an unsupported format.

Provide one small record of each available type:
- Asset/equipment index (pseudonymous asset IDs).
- Governing drawing register (document ID, revision, approved/current state).
- Governing procedure/test-script register (ID, revision, approved/current state).
- Test record/result (test ID, asset ID, outcome, timezone-aware observation time).
- Deficiency/issue log entry (ID and status).
- Corrective action (linked issue ID and status).
- Retest record (linked issue ID, prior result, outcome and time).
- Witness/approval record if required by the owner's checklist.
- A package-level index that states which of the above belong together.
- If this is a pre-test readiness sample: readiness certificate, covered equipment/system IDs, inspection-completion assertion, open-issues-resolved assertion, approver role/authority reference, timezone-aware approval timestamp, and the planned/scheduled test time. Include the linked issue register so any 'all issues resolved' claim can be independently cross-checked.

Use consistent pseudonymous IDs across all records. Preserve relationships and revision differences that are relevant to the evaluation; redact names, project codes, exact locations, customer identifiers, IPs, hostnames, access details and unrelated commercial terms.

## Never include

Credentials, tokens, private keys, live telemetry, control-system exports, network diagrams, sensitive physical-security details, personal data, unredacted customer data, or instructions that could affect equipment or operations. Do not grant access to BMS, EPMS, SCADA, PLC, DCIM or commissioning platforms.

## Authorization and transfer

1. A named data owner confirms in writing that they are authorized to disclose this redacted sample for the stated evaluation.
2. SABLE and the data owner agree the permitted purpose, retention/deletion expectation, delivery channel and whether any output may be retained or shared.
3. Transfer only the approved redacted text package over a mutually agreed channel. Do not send sample records as ordinary email attachments or commit them to a public/private source repository.
4. Stop if permission, provenance, data classification or scope is unclear.

## Evaluation method

- Pin the exact sample file list and compute local SHA-256 digests.
- Map only the declared IDs and fields; preserve source-to-claim traceability.
- Run structural/linkage rules and compare results with the owner's independently labelled expectations.
- Report false positives, missed expected issues, unresolved UNKNOWNs and unsupported formats separately.
- Keep software findings separate from an engineer's actual acceptance decision.

## Output

A short read-only report containing sample scope, input manifest/digests, graph coverage, source-linkage gaps, revision conflicts, deficiency/retest/witness-chain gaps, verdict per finding, known limitations and reviewer feedback. Every finding must point to a specific source record and relationship.

## Stop conditions

No written authorization, unsupported/binary-only evidence, requests for live-system access or write actions, unclear authority to approve acceptance, or unsafe/unlawful data access means STOP.

**This evaluation does not certify design correctness, operational readiness, safety, compliance, authentic signatures, or permission to energize.** The v1 VERIFIED verdict means only that its explicit structural gates passed against the supplied sample.
