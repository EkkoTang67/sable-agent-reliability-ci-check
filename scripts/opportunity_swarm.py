#!/usr/bin/env python3
"""Zero-cost logical opportunity swarm scheduler.

This creates virtual work slots; it does not launch 10,000 LLM sessions or claim
that an opportunity is real. Human/source evidence is required before activation.
Uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

DOMAINS = [
    "ai-agent-billing", "subscription-entitlements", "invoice-exceptions",
    "supplier-onboarding", "data-import-quality", "compliance-evidence",
    "developer-ci", "webhook-reliability", "refund-reconciliation",
    "access-control", "cloud-cost-controls", "smb-reporting",
    "logistics-exceptions", "marketplace-operations", "document-workflows",
    "customer-support-escalations", "sales-ops", "ecommerce-returns",
    "content-rights", "local-business-operations", "procurement",
    "accounting-close", "insurance-claims", "healthcare-admin",
    "education-admin", "construction-change-orders", "real-estate-ops",
    "cybersecurity-evidence", "open-source-maintenance", "api-migrations",
    "mobile-release", "data-privacy-requests", "identity-verification",
    "fraud-review", "payment-failure-recovery", "usage-metering",
    "finops", "ai-evaluation", "agent-permissions", "supply-chain-traceability",
    "contract-renewals", "customer-implementation", "market-data-quality",
    "regulatory-reporting", "accessibility-testing", "localization",
    "knowledge-management", "recruiting-ops", "field-service",
    "returns-and-warranty",
]

MODES = ("prototype_cash", "niche_pain")


def build_manifest(count: int = 10_000) -> Iterable[dict[str, Any]]:
    """Yield deterministic, evenly distributed virtual work slots."""
    if count < 1:
        raise ValueError("count must be >= 1")
    for idx in range(count):
        mode = MODES[idx % len(MODES)]
        # Spread both modes across domains instead of filling one domain at a time.
        domain = DOMAINS[(idx // len(MODES)) % len(DOMAINS)]
        yield {
            "pair_id": f"pair-{idx + 1:05d}",
            "mode": mode,
            "domain": domain,
            "roles": {
                "builder_or_scout": (
                    "prototype_builder" if mode == "prototype_cash" else "pain_scout"
                ),
                "adversarial_verifier": "commercial_reality_auditor",
            },
            "status": "DORMANT",
            "activation": "evidence-gated",
            "llm_calls": 0,
            "cash_budget": 0,
            "evidence_ids": [],
        }


def _truthy_confirmed(value: Any) -> bool:
    return value is True or value == "confirmed"


def screen_record(record: dict[str, Any]) -> dict[str, Any]:
    """Apply hard commercial gates before a human/agent spends build effort."""
    mode = record.get("mode", "prototype_cash")
    reasons: list[str] = []
    reject = False
    score = 0

    if not record.get("source_url", "").startswith("https://"):
        reasons.append("missing_https_source")
    else:
        score += 2

    upfront = record.get("upfront_cost")
    cost_unknown = not isinstance(upfront, (int, float))
    if cost_unknown:
        reasons.append("upfront_cost_unverified")
    elif upfront > 0:
        reject = True
        reasons.append("upfront_cost_required")
    else:
        score += 1

    if record.get("task_open") is False:
        reject = True
        reasons.append("task_not_open")
    elif record.get("task_open") is True:
        score += 2
    else:
        reasons.append("task_status_unverified")

    if mode == "prototype_cash":
        reward = record.get("reward_amount")
        currency = str(record.get("reward_currency", "")).upper()
        non_crypto = currency in {"USD", "EUR", "GBP", "CNY", "RMB", "CAD", "AUD", "JPY"}
        if not isinstance(reward, (int, float)) or reward <= 0 or not non_crypto:
            reasons.append("no_explicit_noncrypto_cash_reward")
        else:
            score += 2

        if not record.get("acceptance_criteria"):
            reasons.append("acceptance_criteria_missing")
        else:
            score += 1

        if not _truthy_confirmed(record.get("funding_status")):
            reasons.append("funding_not_confirmed")
        else:
            score += 2

        if not _truthy_confirmed(record.get("payout_method_confirmed")):
            reasons.append("payout_method_not_confirmed")
        else:
            score += 2

        if record.get("mainland_china_eligible") is not True:
            reasons.append("mainland_china_eligibility_not_confirmed")
        else:
            score += 2

        if reject:
            decision = "REJECT"
            next_action = "Do not work; find another candidate."
        elif any(r in reasons for r in (
            "missing_https_source", "task_status_unverified", "upfront_cost_unverified",
            "no_explicit_noncrypto_cash_reward", "acceptance_criteria_missing",
            "funding_not_confirmed", "payout_method_not_confirmed",
            "mainland_china_eligibility_not_confirmed",
        )):
            decision = "HOLD"
            next_action = "Verify the missing fact from the official source or maintainer before coding."
        else:
            decision = "READY_FOR_SCOPED_ATTEMPT"
            next_action = "Check duplicate/competition status, estimate effort, then attempt only within a time cap."
    elif mode == "niche_pain":
        for key in ("payer_role", "pain_statement", "economic_consequence", "evidence_url"):
            if record.get(key):
                score += 2
            else:
                reasons.append(f"{key}_missing")
        if record.get("observed_workaround"):
            score += 1
        if record.get("buyer_action") in {"paid_pilot", "purchase", "budgeted_trial", "signed_commitment"}:
            score += 4
            decision = "READY_FOR_PROTOTYPE"
            next_action = "Build the smallest prototype tied to that buyer action; cap time and spend."
        elif all(record.get(key) for key in ("payer_role", "pain_statement", "economic_consequence", "evidence_url")):
            decision = "VALIDATE_PAYER"
            next_action = "Seek one observable buyer action, not more generic opinions."
        else:
            decision = "HOLD"
            next_action = "Find primary evidence and identify the actual budget owner."
        if reject:
            decision = "REJECT"
            next_action = "Do not spend on this candidate."
    else:
        decision = "HOLD"
        reasons.append("unknown_mode")
        next_action = "Set mode to prototype_cash or niche_pain."

    return {
        "candidate_id": record.get("candidate_id", "UNASSIGNED"),
        "mode": mode,
        "decision": decision,
        "evidence_score": score,
        "reasons": reasons,
        "next_action": next_action,
        "cash_received": False,
        "note": "A screening decision is not proof of earnings or a payment guarantee.",
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: each JSONL row must be an object")
        rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("seed", help="generate logical worker-pair slots without launching models")
    seed.add_argument("--count", type=int, default=10_000)
    seed.add_argument("--out", type=Path, default=Path("swarm-manifest.jsonl"))
    screen = sub.add_parser("screen", help="screen manually sourced candidate records")
    screen.add_argument("--input", type=Path, required=True, help="candidate records in JSONL")
    screen.add_argument("--out", type=Path, default=Path("screened-candidates.jsonl"))
    args = parser.parse_args(argv)

    try:
        if args.command == "seed":
            rows = list(build_manifest(args.count))
            args.out.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            print(json.dumps({
                "created_slots": len(rows),
                "prototype_cash": sum(r["mode"] == "prototype_cash" for r in rows),
                "niche_pain": sum(r["mode"] == "niche_pain" for r in rows),
                "active_llm_sessions": 0,
                "output": str(args.out),
            }, ensure_ascii=False, indent=2))
        else:
            rows = read_jsonl(args.input)
            screened = [screen_record(row) for row in rows]
            args.out.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in screened),
                encoding="utf-8",
            )
            counts: dict[str, int] = {}
            for row in screened:
                counts[row["decision"]] = counts.get(row["decision"], 0) + 1
            print(json.dumps({"screened": len(screened), "decisions": counts, "output": str(args.out)},
                             ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
