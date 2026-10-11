# SABLE — Data Moat and Public Evidence Base v1.0

## The moat cannot be synthetic-only

SABLE currently has three distinct research assets that must not be conflated:

1. **Public requirement references.** The UFGS Building Commissioning guide, the public USACE Japan Edited Specifications (JES 1.6), USACE ER 1110-345-723, the public NPS DETO 228872 commissioning attachment, and the USDA ARS solicitation 1232SA26Q0704's publicly indexed revised commissioning specification. These describe expected process/artifacts. They are not records that prove a current customer complied or failed.
2. **Independent public audit observations.** Chicago OIG's 2021 audit sampled five public-building projects. It independently rated the overall commissioning documentation for four projects reasonably complete and reported that Williams Park Fieldhouse was missing most required commissioning documents. It also found that recipient access/delivery could fail even when documents were reported to have been provided. The machine-readable extract is in `data/public_audit_cases/chicago_pbc_commissioning_audit_2021.json`. This is a genuine public audit dataset at summary granularity—not raw customer files or document-level graph labels.
3. **Authored synthetic mutation cases.** The 16-case SABLE graph benchmark checks predictable mutations against our own fixture. This is useful for regression tests only; it does not show real-world detection accuracy.
4. **Adjacent public operational measurement data.** The LBNL/DOE public HVAC Fault Detection and Diagnostics dataset contains labeled fault/fault-free series across seven equipment classes, mixing simulation, lab experiments, and field measurements. It has not been downloaded or incorporated. It is not ground truth for readiness/document-delivery failures.

The critical missing asset is **one real, authorized, redacted project package with independent domain-review labels**.

## The differentiating observation

A commissioning evidence state should distinguish:

- **Exists** — a file/record is present.
- **Authoritative** — it comes from an allowed source and has an identified version/approval basis.
- **Correctly bound** — the evidence is linked to the correct asset, governing requirement, test, issue and repetition.
- **Ready for the milestone** — required fields and prerequisite relations are evidenced before the relevant schedule/deadline.
- **Delivered** — a designated recipient or system received the expected artifact.
- **Accessible** — the authorized recipient can retrieve/open the intended version in the actual delivery channel.
- **Accepted/closed** — the authorized decision owner independently confirms the milestone outcome.

These states are not equivalent. The Chicago OIG audit provides a public historical example in which reported document existence/delivery did not reliably establish complete receipt and practical access for building maintenance staff. It does not prove the same issue persists today or that SABLE already detects it.

## Defensibility thesis

A potentially valuable data asset is a licensed, provenance-preserving set of:

`actual project requirement → expected artifact → source/revision → relationship graph → delivery/access proof → independently adjudicated exception label → milestone consequence`

The value would come from years of carefully permissioned and reviewed labels, measured exception accuracy, and trusted use in real closeout/readiness workflows—not from scraping public PDFs or storing customer files without permission.

No project record or label may be reused for training, public examples, other clients, or product marketing unless the permission/contract explicitly authorizes that use. Never publish customer files or sensitive facility details in this repository.

## Current product decision

Keep the pre-test readiness audit as the primary paid test for now. Treat a recipient-access/handover audit as a second evidence-backed hypothesis—not yet a second advertised product—until a buyer confirms a live case and the smallest accepted deliverable. Do not implement a new delivery/access connector before an authorized sample shows which access signals the buyer can safely provide.

## First real data acquisition gate

Request one historical non-sensitive subsystem package with a known adjudicated issue. Prefer either:
- a readiness certificate that must be reconciled with the issue register and test schedule; or
- a handover item where the document was reported as submitted but the intended recipient could not verify access.

Require written data-owner permission, an agreed purpose/retention/deletion rule, a safe transfer channel, an independent reviewer, and a written expectation of allowed label reuse. Use pseudonymous IDs and redacted text sidecars. Record false positives, missed known issues, and UNKNOWNs separately.

## Current evidence ledger

- Public normative/project specification references: present.
- Independent public audit summary data: present at aggregate/project-label granularity.
- Public operational measurement dataset: identified but not downloaded/used.
- SABLE synthetic mutation benchmark: 16 authored cases, CI-tested.
- Authorized current customer sample: 0.
- Independent customer labels: 0.
- Customer-validated accuracy/economic impact: not established.
- R3 settled revenue: 0.
