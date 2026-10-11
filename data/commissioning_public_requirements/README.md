# Public commissioning requirement reference dataset

This folder contains an authored, source-linked requirement register based on the publicly accessible U.S. federal guide specification **UFGS 01 91 00.15 — Building Commissioning** (May 2023, Change 3 dated August 2024). A wider source inventory also catalogues the public USACE Japan Edited Specifications (JES 1.6) and USACE Engineering Regulation ER 1110-345-723 for independent document cross-checking. See [the full SABLE data asset register](../SABLE_DATA_ASSET_REGISTER_V1.json).

This is a genuine public requirements source, **not real project commissioning records**. It supports a requirement taxonomy and traceability benchmark; it does not establish that a particular customer is subject to these clauses, has an open defect, is losing money, or will buy SABLE.

The source explicitly requires project tailoring. A live evaluation must use the actual project-specific specification, owner acceptance checklist, approved submittals and amendments. Each enabled rule must be traceable to that project source and applicability must be confirmed before a PASS/FAIL verdict; otherwise report UNKNOWN.

The register intentionally stores short, authored summaries and page/section pointers, not the source PDF or a copied checklist set. Rights for any downstream redistribution of third-party source materials have not been separately adjudicated.

Excluded sources: ACG material is not used as training or dataset input because ACG's own guideline page states restrictions on entering ACG IP/proprietary content into AI tools and that it may not be used to train AI. See https://www.commissioning.org/commissioningguideline/ .


A separate public LBNL/DOE fault-detection dataset contains labeled operational HVAC series (including simulation, laboratory and field measurements). It is tracked only as an adjacent operational-data resource, not as a validation set for readiness-certificate/document-link detection; see the data asset register for the distinction. Source: https://faultdetection.lbl.gov/data/ .


## Project-specific public specification profile

- [NPS DETO 228872 project commissioning specification profile](project_spec_DETO_228872.json) — public solicitation attachment, issued 2025-08-27; not proof of final award-contract terms or project execution.
- [USDA ARS 1232SA26Q0704 revised commissioning specification profile](project_spec_USDA_ARS_1232SA26Q0704.json) — public solicitation attachment for the Gainesville HVAC repair scope, notice updated September 17, 2026 and inactive since October 8, 2026. The offer deadline has passed; awardee/award status was not confirmed, so this is a requirements reference, not a current buyer lead.
- [Chicago OIG independent audit extract](../public_audit_cases/chicago_pbc_commissioning_audit_2021.json) — independent summary of five completed public-building projects and the finding that document completeness and recipient access were separate issues.
