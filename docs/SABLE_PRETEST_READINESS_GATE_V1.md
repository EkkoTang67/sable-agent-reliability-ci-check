# SABLE — Pre-Test Readiness Evidence Gate v1.0

## The specific decision

**Before an expensive commissioning test is scheduled, is there a source-linked evidence gap that means this subsystem is not yet demonstrably ready under its actual project requirements?**

This is narrower than a general commissioning knowledge graph or turnover-document cleanup. The commercial buyer is the person accountable for a real test-window, readiness certificate, acceptance, handover, retest, or contract milestone.

## Why this wedge has an economic mechanism

The publicly accessible USACE/NAVFAC/AFCEC UFGS Building Commissioning guide describes a readiness certificate before tests are scheduled, tracking commissioning issues to resolution, retesting after deficiencies are corrected, and potential withholding of costs associated with aborted or retested tests. These are **source-derived economic signals, not proof that a specific project is subject to these exact terms or currently losing money**.

Reference and exact page/section mapping:
- data/commissioning_public_requirements/ufgs_01_91_00_15_source_profile.json
- Source: https://www.wbdg.org/FFC/DOD/UFGS/UFGS%2001%2091%2000.15.pdf

For a live project, the actual project's executed specification, owner checklist, approved procedures, amendments, and authority matrix govern. The generic guide cannot replace those documents.

## First paid unit

**Pre-Test Readiness Evidence Audit — one subsystem package.**

Proposed acceptance scope:
- One customer-authorized subsystem and one agreed test/readiness milestone.
- Up to 50 redacted text evidence sidecars, with one graph manifest and the exact project clauses/checklist items selected by the buyer.
- Produce a machine-readable evidence graph and exception register. Every exception cites the requirement ID, source file/record, broken or contradictory relationship, and the question/owner needed to resolve it.
- Separate NOT_VERIFIED from UNKNOWN. A finding is not an engineering rejection; it is a traceable evidence gap for the accountable reviewer.
- Jointly agree success criteria before file intake, including a set of issues the customer reviewer already knows, if available.

Price test:
- **US$2,500** for a bounded review when a live decision, authorized sample, reviewer, and payer path exist.
- **US$5,000** only when there is a real time-bound test/acceptance event, meaningful cost exposure, and a payer who confirms the scope and price in writing.
- These are unvalidated offer hypotheses, not booked revenue, market benchmarks, or guaranteed savings. R3 still means funds settled in the seller-controlled account.

## Current implementation boundary

The current prototype accepts a JSON graph manifest and local UTF-8 text sidecars with explicit key/value field bindings. It does not directly ingest raw CSV/JSON exports, parse PDFs/CAD, connect to source platforms or facility networks, execute tests, validate engineering measurements semantically, authenticate signatures cryptographically, sign a readiness certificate, or authorize test scheduling/energization.

## Data advantage strategy

The defensible asset is not generic text scraped from the web. It is a rights-aware, provenance-preserving corpus composed of:
1. Source-linked project requirement rows confirmed applicable by the buyer.
2. Explicit evidence links and redacted source digests from customer-authorized examples.
3. An independently reviewed label for each finding (true gap, false positive, or unknown).
4. The actual downstream decision impact, where the customer authorizes sharing it.
5. Measured benchmark performance across multiple projects and systems.

No customer artifact or label may be reused for training, publication, or other clients unless the contract/permission explicitly allows it. Do not store project files in the public repository. A moat arises only if this licensed, adjudicated corpus produces better measured outcomes than generic document review.

## Disqualifiers

Kill or defer the opportunity if the buyer cannot identify a current test/readiness/acceptance decision, there is no deadline or meaningful consequence, the customer can safely bypass the check, project rules cannot be confirmed, no one will authorize a redacted sample, no person can approve spend, or the requested work requires unsafe control-system access or a promise of safety certification.

## Commercial evidence ledger

- Public source requirements: available and cited; not customer execution data.
- Adversarial benchmark cases: synthetic mutations; not real-world sensitivity/precision.
- Real authorized project records: not yet acquired.
- Independent customer-labelled findings: not yet acquired.
- Revenue/R3: not established until settled funds are verified.
