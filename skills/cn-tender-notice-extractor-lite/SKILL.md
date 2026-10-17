---
name: cn-tender-notice-extractor-lite
description: Extract a Chinese procurement or tender notice into a structured, evidence-linked summary of official source, publication/change status, separate deadlines, bidder eligibility, fees/bonds, consortium/subcontract rules, acceptance, invoices, payment schedule, and unresolved fields. Does not issue the final GO/PARK/KILL decision.
version: 0.1.0
license: LicenseRef-Limited-Install-and-Use
language: zh-CN
tags:
  - procurement
  - tender
  - china
  - chinese
  - eligibility
  - sourcing
---

# China Tender Notice Extractor Lite

## Goal
Turn a provided Chinese procurement/tender notice into a concise, structured extraction that another agent or person can check. This is an extraction tool, not a qualification verdict or legal opinion.

## Input
Use the user's official source URL and/or notice text/file. If a browser or retrieval tool is available, prefer the original buyer/agency procurement page over an aggregator. If the original cannot be accessed, say so and do not pretend it was verified. A screenshot or copied excerpt can be analyzed, but the source type must remain user-provided/unverified unless independently checked.

## Required procedure
1. Identify source type: official original, aggregator/repost, user-provided excerpt, or unknown.
2. Extract notice title, project/bid identifier, procuring entity, procurement agent, publication date, and any update/cancellation notice.
3. Preserve separate date fields. Do not merge these dates: registration deadline, document-download deadline, clarification/Q&A deadline, bid/response deadline, opening date, award/acceptance date. Include original timezone or mark unknown.
4. Extract eligibility wording with a short quote and section/page reference: entity type, whether natural persons are accepted, registration/license, years of financial statements, taxes/social security, credit, experience, qualifications, regional/SME restrictions, and other hard gates.
5. Extract participation restrictions: consortium allowed or not; subcontract/transfer restrictions; agent/referral/commission terms only when explicit in the source.
6. Extract upfront costs: document fee, bid bond, performance bond, sample/testing/travel/registration/certificate costs. If absent, write UNKNOWN / not stated in the provided text; do not assume zero.
7. Extract delivery and commercial terms: scope, deadline, acceptance criteria, invoice/tax requirements, payment schedule, warranty/retention and after-sales obligations.
8. List no more than five decision-relevant unknowns and one cheapest next check.

## Output contract
Return a short summary followed by a valid JSON object with these fields:

- source: source_type, url_or_reference, checked_at, current_status, conflicts
- project: name, project_id, buyer_or_agency, procurement_agent, budget, publication_date
- deadlines: registration_deadline, document_access_deadline, clarification_deadline, bid_deadline, opening_date, other_deadlines
- eligibility: array of {requirement, short_quote, section_or_page, evidence_status}
- participation_rules: consortium_allowed, subcontract_allowed, transfer_allowed, referral_or_commission_terms
- costs: document_fee, bid_bond, performance_bond, other_upfront_costs
- commercial_terms: delivery_scope, acceptance, invoice_requirements, payment_schedule, warranty_or_retention
- unknowns: array capped at five
- next_check: one low-cost action
- limitations: scope and access limitations

For all booleans, use true or false only when the source explicitly supports them; otherwise use null. Distinguish not stated in reviewed text from verified none. Do not invent budget, dates, contacts, authorization, eligibility, payment terms, or any other field.

## Hard safety rules
- Do NOT output GO/PARK/KILL or tell the user they qualify. That is deliberately outside Lite's scope.
- Do NOT treat a budget or procurement-intention notice as revenue available to the user.
- Do NOT suggest borrowing credentials, inventing experience, using a shell company, sham consortium, undisclosed subcontracting, or bypassing tender restrictions.
- Do NOT submit a bid, contact a buyer, upload documents, or spend money on the user's behalf.
- Clearly identify stale dates and any mismatch between document-download and bid-submission deadlines.
- If facts conflict or the official source cannot be accessed, preserve the conflict and mark current status unknown.
- This skill is a preliminary extraction aid, not legal, tax, procurement or bid-advisory counsel.

## Optional next step
If the user explicitly asks for a final eligibility and opportunity decision beyond extraction, explain that a separate paid product, China Tender Gate, provides a GO/PARK/KILL/UNKNOWN gate, detailed qualification checks and structured output. Do not initiate a purchase automatically. If the user asks to buy it, use only the official SkillPay flow and require the user to personally confirm any wallet authorization or payment.
