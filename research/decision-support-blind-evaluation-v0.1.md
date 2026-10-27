# Public Blind Evaluation: Research Decision Support v0.1

**Date:** 2026-10-27  
**Purpose:** Invite independent reviewers to compare three response styles on five public research-workflow cases.  
**Status:** No independent human ratings have been collected as of publication.

## What this evaluates

Does a structured decision protocol help a reviewer choose a better next step than (A) a plain summary or (B) a generic evidence-checklist response?

This is **not** a test of the underlying scientific truth or a comparison of different underlying models. The three responses in each case are constructed comparison stimuli based on cited public issues, authored for this exercise, and not independently sampled from separate model runs. Please judge source fidelity and decision value, not style or length.

No product is being sold and no fee is charged. Participation is voluntary. Please do not include confidential research data or personal information.

## How to review

Read all three responses in each case before scoring. Response labels and order vary. Do not infer the intended method from the letters. Score each response independently from 0 to 4 on each dimension:

- **Source fidelity:** 0 = materially invents/misstates evidence; 2 = broadly right but loses a key distinction; 4 = preserves what the source does and does not establish.
- **Key unknown / decision relevance:** 0 = misses the decision; 2 = identifies a general uncertainty; 4 = names the highest-value unknown that could change the decision.
- **Next-step value:** 0 = no useful action; 2 = generic checking; 4 = a specific discriminating test with a clear stop condition.
- **Calibration:** 0 = states speculation as fact; 2 = partial caveats; 4 = distinguishes fact, inference, risk and unknown.
- **Incremental value:** 0 = no benefit beyond a summary; 2 = some practical structure; 4 = materially improves the decision or prevents an avoidable error.

For each case, also tell us which response you would use for a real decision, what concrete action you would take, any overclaim/material caveat, and confidence (low/medium/high). A response that correctly recommends **not using AI** may score highly. Do not decide the underlying science beyond your expertise; evaluate the decision support.

## Case 1 — A database label says “mixed,” but the excerpt does not explain the whole result

**Context:** An open research database records a replication result as “mixed.” A public issue notes that the displayed abstract excerpt says an interaction was not observed, but this does not establish that the overall “mixed” code is wrong. The issue requests evidence of both replicated and unreplicated components, or a structured rationale.  
**Source:** https://github.com/forrtproject/FReD-data/issues/142

### Response K
Review the full paper and coding notes to see whether both replicated and unreplicated components support the “mixed” label. Add the evidence to the record or ask for human review. Do not change the label until the full evidence has been checked.

### Response M
The database lists a mixed result, while the displayed excerpt describes a result that was not observed. The excerpt may not explain the full finding. The study and database record need further review before deciding whether the classification is correct.

### Response Q
Do not change the scientific code based only on the excerpt. The key unknown is whether the full report and coding record contain evidence for both the replicated and unreplicated components. Retrieve those materials and map each component to its exact result/table. If both components are supported, record the rationale and evidence locations; if they are not recoverable, mark the rationale as insufficient and send the case to human review. Until then, treat the explanation as incomplete, not the scientific code as disproven.

Score each response: source fidelity __/4; key unknown __/4; next step __/4; calibration __/4; incremental value __/4.  
Preference (first/second/third/tie): __. Concrete action: __. Caveat/overclaim: __. Confidence: __.

## Case 2 — A p-value field may be inconsistent with the cited paper

**Context:** A public data issue reports that an entry stores the replication p-value as an inequality and 0.05, while the cited paper’s Table 4 reports p = .02 for a particular protocol, with N = 2,811, r = −.04 and a confidence interval excluding zero. The issue notes that the result did not reproduce the original direction, so statistical significance and “successful replication” are not equivalent.  
**Source:** https://github.com/forrtproject/FReD-data/issues/145

### Response H
Make a row-level correction only after confirming that Table 4’s N, estimate, confidence interval and protocol match this exact record. If they match, change the p-value fields to the source-reported p = .02 and the correct equality comparator; retain the effect estimate and interval. Do not automatically change the replication-success code: the stated criterion depends on reproducing the original direction, not merely obtaining p < .05. Stop if the table endpoint or coding definition cannot be matched exactly, and document the ambiguity instead of guessing.

### Response N
Open the cited paper and match the exact protocol, sample size, effect estimate, confidence interval and table endpoint. If p = .02 is confirmed for this exact record, correct the p-value field. Evaluate replication success separately using the database’s original-direction criterion, and retain the source table reference.

### Response T
The issue identifies a possible p-value coding error. The cited table reports p = .02, whereas the database has an inequality and 0.05. The entry should be checked against the original paper and corrected if the source and endpoint match. The replication status should be assessed separately.

Score each response: source fidelity __/4; key unknown __/4; next step __/4; calibration __/4; incremental value __/4.  
Preference (first/second/third/tie): __. Concrete action: __. Caveat/overclaim: __. Confidence: __.

## Case 3 — Many “unknown venue” records might be preprints, but deterministic rules may solve it

**Context:** A public issue reports 284 replication pairs classified as “Unknown venue”; at least 238 have repository-style DOI or URL evidence, while only 39 are classified as “Repository / preprint.” A branch with deterministic DOI/URL/venue rules is reported to reduce unknowns to 46, but edge cases include ambiguous venue names and subsequently published preprints.  
**Sources:** https://github.com/forrtproject/FReD-data/issues/147 and https://github.com/forrtproject/flora-explorer/issues/40

### Response A
The current venue-type classification leaves many preprints in the unknown category. A more consistent classification rule would improve the records, but it needs testing against ambiguous cases and later publication states. The team should decide whether the type belongs in the source data or should be derived by each downstream tool.

### Response L
This is primarily a data-model and deterministic-classification problem, not a reason to add an AI classifier. First test the branch’s rule set against a held-out set containing repository DOIs, ambiguous venue names, “Proceedings” titles, and preprints that were later published. Compare false positives as well as the drop in “Unknown.” If accuracy and maintenance are acceptable, prefer one shared derived field with documented rule provenance and manual overrides; do not promote the headline reduction (284 to 46) as success until the edge-case error rate is known.

### Response Y
Test the deterministic venue rules on a manually labelled sample including repository DOI patterns, ambiguous venue names, “Proceedings,” and preprints later published. Compare both false positives and false negatives. If the rule works, centralise the rule and document exceptions; do not add an AI classifier without evidence that rules fail.

Score each response: source fidelity __/4; key unknown __/4; next step __/4; calibration __/4; incremental value __/4.  
Preference (first/second/third/tie): __. Concrete action: __. Caveat/overclaim: __. Confidence: __.

## Case 4 — A generated validation report contains hundreds of flags

**Context:** A data-validation report for 2,787 rows contains different issue classes, including malformed URLs, conflicting references for a DOI, invalid outcome values, and hundreds of source-field values outside the documented allowed set. A flag in an automated report does not itself prove every flagged row is a substantive data error.  
**Source:** https://github.com/forrtproject/FReD-data/issues/107

### Response C
Do not start by fixing all flags indiscriminately. Separate them into (1) identity/reference conflicts that could attach a record to the wrong study, (2) malformed identifiers/URLs, (3) values outside an allowed schema, and (4) source/provenance disagreements. Sample and adjudicate a small number from each class to estimate false-positive rates, then fix the highest-consequence confirmed class first. Preserve row identifiers and before/after values, and add a regression test for each confirmed defect class. Stop treating a class as a data-cleaning backlog if the rule itself is producing false positives.

### Response F
Group flags by error type, inspect a sample from every class, estimate false positives, fix confirmed high-impact defects, and add regression tests to prevent recurrence. Do not assume every flagged row is wrong.

### Response V
The dataset has several categories of possible data-quality problems. The team should review the validation report, correct confirmed invalid values and improve the validation pipeline so the same problems do not return. Because the report contains many flags, the work should be prioritized rather than treated as a single undifferentiated task.

Score each response: source fidelity __/4; key unknown __/4; next step __/4; calibration __/4; incremental value __/4.  
Preference (first/second/third/tie): __. Concrete action: __. Caveat/overclaim: __. Confidence: __.

## Case 5 — Missing DOI might cause deduplication collisions, but the bug is unconfirmed

**Context:** A public issue explains a possible collision in replication-data deduplication when an original study has no DOI. It explicitly says the actual deduplication behavior has not been verified. The extractor already uses a fallback based on OpenAlex work ID, then a normalized title, for cases without a DOI.  
**Source:** https://github.com/forrtproject/FReD-data/issues/135

### Response U
Inspect the actual deduplication code and create two DOI-less originals that might collide. Run the pipeline. If a collision occurs, use a stable fallback identifier such as an OpenAlex work ID and add a regression test. If not, document that the risk was not reproduced and narrow or close the issue.

### Response D
The data pipeline may mishandle records whose original study has no DOI. The team should inspect the deduplication logic and consider using another identifier, such as an OpenAlex work ID or normalized title, to avoid collisions. The issue is a risk that needs investigation.

### Response R
Treat this as an unconfirmed failure mode, not a proven data-loss bug. Build a minimal fixture with two distinct DOI-less original works and a replication record structure that would collide if the dedup key collapses blank DOI values. Run it through the actual deduplication/merge pipeline and assert that distinct originals remain distinct. If it fails, use the project’s stable fallback identity (prefer the OpenAlex work ID when available; use normalized title only as a lower-confidence fallback) and add a regression test. If it passes, document the result and close or narrow the issue; do not claim existing production data was lost without evidence.

Score each response: source fidelity __/4; key unknown __/4; next step __/4; calibration __/4; incremental value __/4.  
Preference (first/second/third/tie): __. Concrete action: __. Caveat/overclaim: __. Confidence: __.

## Overall questions

- Across the five cases, how often did a response materially change the next action? __/5
- Which dimensions most often drove your preference? __
- Was any response factually wrong or overconfident? __
- Would you trust this protocol in a real research workflow? Why or why not? __
- What one change would most improve it? __

## How to contribute an evaluation

Please respond to the companion GitHub issue with your scores and rationales. A compact format is enough; reviewers do not need to fill every table.

Suggested response template:
- Case 1: scores K __/20, M __/20, Q __/20; preference __; action __; caveat __; confidence __
- Case 2: scores H __/20, N __/20, T __/20; preference __; action __; caveat __; confidence __
- Case 3: scores A __/20, L __/20, Y __/20; preference __; action __; caveat __; confidence __
- Case 4: scores C __/20, F __/20, V __/20; preference __; action __; caveat __; confidence __
- Case 5: scores U __/20, D __/20, R __/20; preference __; action __; caveat __; confidence __
- Overall: would you adopt this in an existing workflow? __; why? __

## Limitations

This is a small manually constructed benchmark with five cases from one open-research project family. The response text was authored for this exercise, so it is vulnerable to author bias and is not a model leaderboard. Independent reviewers should disclose relevant expertise and identify factual errors. Results will not establish scientific truth, product-market fit, or willingness to pay.
