# Real Sample Acquisition Log — 2026-10-11

Purpose: obtain one explicitly authorized, redacted, historical commissioning/turnover sample to test SABLE against independently adjudicated reality. Email send is not delivery, reply, permission, customer evidence, sale, or R3.

## Current request and status

| Target | Why this target | Contact route | Request | Observed status |
|---|---|---|---|---|
| ETHYCO | Public scope includes independent commissioning, Level 5 IST and turnover package | Matt@ethyco.com | One bounded read-only evidence-closure pilot; previously proposed US$5,000 | AgentMail shows one outbound message labelled `delayed`; no reply in the observed thread. Delivery/read status is not confirmed. |
| 2N Mission Critical | Public scope includes hyperscale commissioning, Level 0–5, IST and turnover | info@2nmcx.com | One system/turnover package; ask for owner, safe sample authorization path, deadline and payer path | AgentMail shows one outbound request on 2026-10-11; no reply in the observed thread. Delivery/read status is not confirmed. |
| JAGS Assurance | Public scope includes data-center commissioning QA/QC and discusses turnover package evidence | info@jagsassurance.com | First request for 8–15 authorized redacted UTF-8 text/CSV/JSON records and an independently known gap; no attachment requested | AgentMail accepted outbound message on 2026-10-11. No reply observed at send time. Delivery/read status remains unconfirmed. |

Public research references:
- ETHYCO services/contact: https://ethyco.com/contact.html
- 2N Mission Critical services/contact: https://2nmissioncritical.com/services
- JAGS Assurance data center commissioning QA/QC: https://jagsassurance.com/services/data-center-commissioning-qa-qc

## Data assets currently available

- Public normative/reference layer: UFGS 01 91 00.15 source-linked requirement register, plus a source catalog entry for the public USACE Japan Edited Specifications (JES 1.6) and USACE ER 1110-345-723. These are requirement/specification references, not evidence that a customer project followed them.
- Public operational benchmark reference: LBNL Fault Detection and Diagnostics data catalog, with labeled fault/fault-free HVAC series across seven equipment classes and a mixture of simulation, lab and field measurements. The data has not been downloaded or incorporated, and it is not ground truth for document readiness closure.
- Executable benchmark: 16 authored synthetic graph cases, checked in CI; these test only declared mutation behavior.
- Critical missing asset: a customer-authorized historical subsystem sample plus independent review labels.

See [SABLE data asset register](../data/SABLE_DATA_ASSET_REGISTER_V1.json) for provenance, evidence class, rights caution and relevance. No class may be presented as another.

## Sample acceptance gate

Do not accept or process a real package until the data owner confirms written authority, the permitted purpose and retention/deletion terms are agreed, and a safe transfer channel is agreed. Do not place customer files in this public repository or ordinary email attachments. V1 directly reads a JSON graph manifest and local UTF-8 text sidecars with key/value fields. It does not directly parse raw CSV/JSON exports, binary PDF/CAD, or source systems; a documented manual normalization step for redacted fields would require prior agreement.

Desired sample:
- One completed and non-sensitive subsystem package.
- Approximately 8–15 redacted records with stable pseudonymous IDs.
- Asset index, governing drawing/procedure revision, test result/time, issue/deficiency, corrective action, retest, witness/sign-off record if required, package index.
- Prefer one known, already-adjudicated missing link or mismatch, with reviewer-labelled expected result.
- No credentials, IP/network details, exact site identifiers, live telemetry, personal data or unredacted client data.

## Evidence ledger

- FACT: current prototype is available as draft PR #7; latest observed CI run 38118402441 passed 22 unit tests, the synthetic CLI fixture, and the 16-case authored mutation benchmark with `failed: 0`.
- FACT: outbound requests were created to the three recipients above.
- FACT: as of the latest inbox read in this turn, those target threads show outbound-only messages; no recipient reply is visible. ETHYCO's thread retains a `delayed` label. Delivery/read state is unconfirmed.
- UNKNOWN: whether any recipient received/read the messages, whether any will authorize sample sharing, whether any real evidence gap exists in their workflow, and whether a payer would buy a pilot.
- FACT: no authorized real project sample has been received; no customer evaluation has been completed; R3 remains 0.

## Decision rule

Do not add source-system adapters or expand document parsing until one real authorized sample is obtained and reviewed with an accountable domain reviewer. If targets do not respond, prefer a verified warm/partner path or a target with a live handover deadline over indiscriminately increasing email volume.
