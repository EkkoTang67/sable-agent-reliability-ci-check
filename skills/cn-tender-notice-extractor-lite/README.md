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

```bash
npx skills add EkkoTang67/sable-agent-reliability-ci-check --skill cn-tender-notice-extractor-lite
```

Review the skill and the license before installing. Use only current official source material for high-stakes procurement decisions.

## Feedback and error reports

**[Share a use result or product need](https://github.com/EkkoTang67/sable-agent-reliability-ci-check/issues/new?template=feedback.yml)** · **[Report an error or important omission](https://github.com/EkkoTang67/sable-agent-reliability-ci-check/issues/new?template=bug_report.yml)**

Issues are public. Do not post personal information, account credentials, confidential procurement files, or customer secrets. Prefer public official source URLs and minimal redacted excerpts. A report is a signal to investigate, not automatically a verified fact.

We use feedback to decide what to fix, what to test next, and whether the deeper decision product solves a real paid need. Installs, compliments, and expressions of interest are not counted as settled revenue.

The operating rules are documented in [Feedback-to-Cash Loop v1.0](https://github.com/EkkoTang67/sable-agent-reliability-ci-check/blob/main/docs/feedback/FEEDBACK_TO_CASH_LOOP_V1.md).

## Related paid product
For a stricter final opportunity gate with GO/PARK/KILL/UNKNOWN decisions, detailed qualification rules, a JSON output schema, and regression examples, see China Tender Gate on SkillPay. Search for the exact product name in SkillPay. This Lite skill does not trigger purchases automatically.

## License
This directory is governed only by [LICENSE.md](LICENSE.md): install-and-use rights for the unmodified package, with no modification or redistribution grant. Other files in the repository are outside this license.
