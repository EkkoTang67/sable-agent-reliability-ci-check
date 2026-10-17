# China Tender Notice Extractor Lite

A narrow Agent Skill that extracts key facts from Chinese procurement/tender notices into a structured, evidence-linked record.

## What it does
- Separates document access, clarification, and bid-submission deadlines.
- Extracts bidder entity/qualification clauses and section references.
- Records fees/bonds, consortium/subcontract rules, acceptance and payment terms.
- Keeps unknowns explicit and produces a JSON-shaped summary.

## What it does not do
- It does not make a final GO/PARK/KILL decision or provide legal advice.
- It does not guarantee eligibility, tender success, orders, or revenue.
- It does not bypass legal entity requirements, no-subcontract rules, or other tender conditions.

## Install
For a supported Agent Skills client, install the selected skill from this public repository:

\`\`\`bash
npx skills add EkkoTang67/sable-agent-reliability-ci-check --skill cn-tender-notice-extractor-lite
\`\`\`

Review the skill and the license before installing. Use only current official source material for high-stakes procurement decisions.

## Related paid product
For a stricter final opportunity gate with GO/PARK/KILL/UNKNOWN decisions, detailed qualification rules, a JSON output schema, and regression examples, see China Tender Gate on SkillPay. Search for the exact product name in SkillPay. This Lite skill does not trigger purchases automatically.

## License
This directory is governed only by [LICENSE.md](LICENSE.md): install-and-use rights for the unmodified package, with no modification or redistribution grant. Other files in the repository are outside this license.
