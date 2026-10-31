#!/usr/bin/env python3
"""Deterministic, buyer-rule-driven evidence workbench. Synthetic demo; no document authenticity claims."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


SUPPORTED_CHECKS = {"required", "same", "date_order", "numeric_equal"}


def _path_value(records: dict[str, dict[str, Any]], path: dict[str, str]):
    record = records.get(path.get("record_id", ""))
    if record is None:
        return None, None, "record_not_found"
    field = path.get("field", "")
    if field not in record.get("fields", {}) or record["fields"][field] in (None, ""):
        return None, record.get("source_ref"), "field_missing"
    return record["fields"][field], record.get("source_ref"), None


def _check_result(check: dict[str, Any], records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    check_id = check.get("check_id", "UNNAMED")
    check_type = check.get("type")
    paths = check.get("paths", [])
    if check_type not in SUPPORTED_CHECKS:
        raise ValueError(f"unsupported check type: {check_type}")
    min_paths = 1 if check_type == "required" else 2
    if len(paths) < min_paths:
        raise ValueError(f"{check_id}: {check_type} requires at least {min_paths} path(s)")

    observed, source_refs, missing = [], [], []
    for path in paths:
        value, source_ref, reason = _path_value(records, path)
        observed.append(value)
        source_refs.append(source_ref)
        if reason:
            missing.append({"record_id": path.get("record_id"), "field": path.get("field"), "reason": reason})

    if missing:
        status = "UNKNOWN"
        detail = "Required source record or field is missing; no value was inferred."
    elif check_type == "required":
        status = "PASS"
        detail = "Required field is present in the referenced source record."
    elif check_type == "same":
        normalized = [str(v).strip() for v in observed]
        status = "PASS" if len(set(normalized)) == 1 else "GAP"
        detail = "Referenced values match." if status == "PASS" else "Referenced values conflict."
    elif check_type == "date_order":
        try:
            earlier, later = date.fromisoformat(str(observed[0])), date.fromisoformat(str(observed[1]))
            status = "PASS" if earlier <= later else "GAP"
            detail = "Date sequence is valid." if status == "PASS" else "Later-date field precedes earlier-date field."
        except (TypeError, ValueError):
            status, detail = "UNKNOWN", "Date value is not a valid ISO YYYY-MM-DD date."
    else:  # numeric_equal
        try:
            numbers = [Decimal(str(v)) for v in observed]
            tolerance = Decimal(str(check.get("tolerance", "0")))
            status = "PASS" if max(numbers) - min(numbers) <= tolerance else "GAP"
            detail = "Numeric values are within the buyer-specified tolerance." if status == "PASS" else "Numeric values differ beyond the buyer-specified tolerance."
        except (InvalidOperation, ValueError):
            status, detail = "UNKNOWN", "A numeric value or tolerance could not be parsed."

    return {
        "check_id": check_id,
        "type": check_type,
        "description": check.get("description", ""),
        "status": status,
        "detail": detail,
        "observed_values": observed,
        "source_refs": source_refs,
        "missing": missing,
    }


def evaluate_package(package: dict[str, Any], raw_bytes: bytes | None = None) -> dict[str, Any]:
    if package.get("schema_version") != "evidence-workbench.input.v1":
        raise ValueError("schema_version must be evidence-workbench.input.v1")
    if not package.get("engagement_id") or not package.get("buyer_rule_version"):
        raise ValueError("engagement_id and buyer_rule_version are required")
    case_ids = [c.get("case_id") for c in package.get("cases", [])]
    if not case_ids or any(not x for x in case_ids) or len(set(case_ids)) != len(case_ids):
        raise ValueError("cases must have unique, non-empty case_id values")

    case_reports = []
    for case in package["cases"]:
        record_list = case.get("records", [])
        record_ids = [r.get("record_id") for r in record_list]
        if any(not x for x in record_ids) or len(set(record_ids)) != len(record_ids):
            raise ValueError(f"{case['case_id']}: record_id values must be unique and non-empty")
        records = {r["record_id"]: r for r in record_list}
        checks = [_check_result(c, records) for c in case.get("checks", [])]
        if not checks:
            raise ValueError(f"{case['case_id']}: at least one check is required")
        statuses = {c["status"] for c in checks}
        verdict = "UNKNOWN" if "UNKNOWN" in statuses else ("GAP" if "GAP" in statuses else "PASS")
        case_reports.append({
            "case_id": case["case_id"],
            "case_type": case.get("case_type", ""),
            "verdict": verdict,
            "checks": checks,
        })

    counts = {s: sum(1 for c in case_reports if c["verdict"] == s) for s in ("PASS", "GAP", "UNKNOWN")}
    overall = "UNKNOWN" if counts["UNKNOWN"] else ("GAP" if counts["GAP"] else "PASS")
    payload_bytes = raw_bytes if raw_bytes is not None else json.dumps(package, sort_keys=True).encode("utf-8")
    return {
        "report_schema_version": "evidence-workbench.report.v1",
        "workbench_version": "0.1.0",
        "engagement_id": package["engagement_id"],
        "domain": package.get("domain", "unspecified"),
        "buyer_rule_version": package["buyer_rule_version"],
        "input_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "overall_verdict": overall,
        "case_counts": counts,
        "case_reports": case_reports,
        "limitations": [
            "Checks only the supplied fields against the buyer-specified rules.",
            "A PASS does not authenticate a source, prove physical condition, establish legal entitlement, or certify completeness beyond the declared checks.",
            "UNKNOWN means evidence or parsing is insufficient; missing values are never inferred.",
            "All demo fixtures are synthetic. No live customer, insurer, carrier, OEM, or equipment records are included.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Evidence Workbench Report — {report['engagement_id']}",
        "",
        f"- Domain: {report['domain']}",
        f"- Buyer rule version: {report['buyer_rule_version']}",
        f"- Workbench version: {report['workbench_version']}",
        f"- Overall verdict: **{report['overall_verdict']}**",
        f"- Input SHA-256: `{report['input_sha256']}`",
        "",
        "## Case summary",
        "",
        "| Case | Type | Verdict | Checks |",
        "|---|---|---|---:|",
    ]
    for case in report["case_reports"]:
        lines.append(f"| {case['case_id']} | {case['case_type']} | **{case['verdict']}** | {len(case['checks'])} |")
    lines.extend(["", "## Check details", ""])
    for case in report["case_reports"]:
        lines.extend([f"### {case['case_id']} — {case['verdict']}", ""])
        for check in case["checks"]:
            lines.append(f"- **{check['check_id']} — {check['status']}**: {check['detail']}")
            lines.append(f"  - Source references: {', '.join(str(x) for x in check['source_refs'] if x) or 'None'}")
            if check["missing"]:
                lines.append(f"  - Missing: {json.dumps(check['missing'], ensure_ascii=False)}")
        lines.append("")
    lines.extend(["## Limitations", ""])
    lines.extend([f"- {item}" for item in report["limitations"]])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    package = json.loads(raw.decode("utf-8"))
    report = evaluate_package(package, raw)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    markdown = render_markdown(report)
    if args.json_out:
        args.json_out.write_text(rendered, encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.write_text(markdown, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
