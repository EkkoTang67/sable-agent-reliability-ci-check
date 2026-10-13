#!/usr/bin/env python3
"""SABLE x402 Payment-to-Outcome Closure auditor (offline, read-only).

Audits an evidence dossier. It does not submit payments, call paid endpoints,
assume supplied evidence is authentic, or equate settlement with delivery.
Python standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "sable.x402_closure.v0.1.0"
VERDICTS = {"VERIFIED", "NOT_VERIFIED", "UNKNOWN"}


def _norm(value: Any) -> str:
    return "" if value is None else str(value).strip().lower()


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _status(verdict: str, reason: str, **details: Any) -> dict[str, Any]:
    return {"verdict": verdict, "reason": reason, **details}


def _field_mismatch(expected: Any, observed: Any) -> bool:
    return _norm(expected) != _norm(observed)


def assess_settlement(expected: dict[str, Any], observed: dict[str, Any] | None) -> dict[str, Any]:
    if not observed:
        return _status("UNKNOWN", "No settlement observation supplied.")
    required = ("transaction_hash", "status", "network", "recipient", "amount", "asset", "asset_contract")
    missing = [key for key in required if observed.get(key) in (None, "")]
    if missing:
        return _status("UNKNOWN", "Settlement evidence is incomplete.", missing_fields=missing, source_url=observed.get("source_url"))
    contradictions: list[str] = []
    if _field_mismatch(expected.get("transaction_hash"), observed.get("transaction_hash")):
        contradictions.append("transaction_hash_mismatch")
    if _norm(observed.get("status")) not in {"success", "ok", "confirmed"}:
        if _norm(observed.get("status")) in {"failed", "reverted", "error", "dropped"}:
            contradictions.append("settlement_not_successful")
        else:
            return _status("UNKNOWN", "Settlement status is not a recognized terminal success/failure.", observed_status=observed.get("status"), source_url=observed.get("source_url"))
    for key in ("network", "recipient", "amount", "asset", "asset_contract"):
        if expected.get(key) is not None and _field_mismatch(expected[key], observed.get(key)):
            contradictions.append(f"{key}_mismatch")
    if contradictions:
        return _status("NOT_VERIFIED", "Settlement evidence contradicts the expected payment.", contradictions=contradictions, source_url=observed.get("source_url"))
    return _status("VERIFIED", "The supplied settlement observation matches the expected transaction fields.", scope="settlement_fields_only", source_url=observed.get("source_url"), independent_source=bool(observed.get("independent_source", False)))


def assess_service_binding(expected: dict[str, Any], observed: dict[str, Any] | None) -> dict[str, Any]:
    if not observed:
        return _status("UNKNOWN", "No service-side record supplied.")
    if not observed.get("transaction_hash"):
        latest_hash = observed.get("latest_transaction_hash")
        if isinstance(latest_hash, str) and latest_hash:
            return _status(
                "UNKNOWN",
                "The service snapshot advertises metadata for a different latest transaction; no service-side record binds the requested transaction to this endpoint.",
                source_url=observed.get("source_url"),
                latest_transaction_hash=latest_hash,
                advertised_endpoint=observed.get("endpoint"),
                advertised_price_usd=observed.get("price_usd"),
                scope="latest_metadata_not_transaction_bound",
            )
        return _status("UNKNOWN", "Service-side record does not expose a transaction hash.", source_url=observed.get("source_url"))
    if _field_mismatch(expected.get("transaction_hash"), observed.get("transaction_hash")):
        return _status("NOT_VERIFIED", "Service-side metadata points to a different transaction.", source_url=observed.get("source_url"))
    if expected.get("endpoint") and not observed.get("endpoint"):
        return _status("UNKNOWN", "Service-side metadata does not identify an endpoint, so the intended service cannot be bound.", source_url=observed.get("source_url"))
    if expected.get("endpoint") and observed.get("endpoint") and _field_mismatch(expected["endpoint"], observed["endpoint"]):
        return _status("NOT_VERIFIED", "Service-side metadata points to a different endpoint.", source_url=observed.get("source_url"))
    price_usd = observed.get("price_usd")
    if price_usd is not None and expected.get("amount") is not None and _norm(expected.get("asset")) == "usdc":
        try:
            if Decimal(str(price_usd)) != Decimal(str(expected["amount"])):
                return _status("NOT_VERIFIED", "Service-advertised USD price conflicts with the expected native USDC payment amount.", expected_amount=expected.get("amount"), observed_price_usd=str(price_usd), source_url=observed.get("source_url"))
        except (InvalidOperation, ValueError, TypeError):
            return _status("UNKNOWN", "Service-advertised price is not a valid decimal amount.", source_url=observed.get("source_url"))
    if observed.get("valid") is False:
        return _status("NOT_VERIFIED", "Service-side evidence marks this record invalid.", source_url=observed.get("source_url"))
    if observed.get("valid") is not True:
        return _status("UNKNOWN", "Service-side evidence does not assert a valid record.", source_url=observed.get("source_url"))
    return _status("VERIFIED", "Transaction and service metadata correlate; this is not proof of semantic delivery.", scope="metadata_only", source_url=observed.get("source_url"), match_score=observed.get("match_score"), independent_source=bool(observed.get("independent_source", False)))


def assess_delivery(expected: dict[str, Any], observed: dict[str, Any] | None) -> dict[str, Any]:
    if not observed:
        return _status("UNKNOWN", "No response receipt or authoritative downstream readback supplied.")
    readback = observed.get("downstream_readback")
    if isinstance(readback, dict) and readback.get("authoritative") is True:
        if _field_mismatch(expected.get("transaction_hash"), readback.get("transaction_hash")):
            return _status("NOT_VERIFIED", "Authoritative readback is bound to a different transaction.", source_url=readback.get("source_url"))
        if readback.get("outcome") == "contradicted":
            return _status("NOT_VERIFIED", "Authoritative downstream readback contradicts the required outcome.", source_url=readback.get("source_url"))
        if readback.get("outcome") == "satisfied":
            return _status("VERIFIED", "Authoritative downstream readback supports the required outcome.", scope="downstream_state", source_url=readback.get("source_url"))
    receipt = observed.get("response_receipt")
    if not isinstance(receipt, dict):
        return _status("UNKNOWN", "No response receipt is available; HTTP status/settlement metadata alone cannot prove content delivery.", unpaid_probe_status=observed.get("unpaid_probe_status"))
    if _field_mismatch(expected.get("transaction_hash"), receipt.get("transaction_hash")):
        return _status("NOT_VERIFIED", "Response receipt is bound to a different transaction.", source_url=receipt.get("source_url"))
    if receipt.get("authoritative") is not True:
        return _status("UNKNOWN", "Response receipt is not identified as an authoritative source.", source_url=receipt.get("source_url"))
    raw_body = receipt.get("response_body")
    declared_digest = receipt.get("response_sha256")
    if raw_body is None or not declared_digest:
        return _status("UNKNOWN", "Receipt lacks the response bytes or a declared response digest.", source_url=receipt.get("source_url"))
    actual_digest = hashlib.sha256(str(raw_body).encode("utf-8")).hexdigest()
    if _field_mismatch(declared_digest, actual_digest):
        return _status("NOT_VERIFIED", "Response body digest does not match the receipt digest.", expected_digest=declared_digest, actual_digest=actual_digest, source_url=receipt.get("source_url"))
    if receipt.get("outcome") != "satisfied":
        return _status("UNKNOWN", "Response integrity matches, but the required semantic outcome was not independently established.", response_sha256=actual_digest, source_url=receipt.get("source_url"))
    return _status("VERIFIED", "An authoritative receipt binds the response bytes and required outcome to the expected transaction.", response_sha256=actual_digest, source_url=receipt.get("source_url"))


def assess(case: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected") or {}
    obs = case.get("observations") or {}
    required = ("transaction_hash", "network", "recipient", "amount", "asset", "asset_contract", "endpoint")
    missing = [key for key in required if expected.get(key) in (None, "")]
    if missing:
        raise ValueError(f"case.expected missing required fields: {', '.join(missing)}")
    components = {
        "settlement": assess_settlement(expected, obs.get("settlement")),
        "service_binding": assess_service_binding(expected, obs.get("service_record")),
        "delivery": assess_delivery(expected, obs.get("delivery")),
    }
    vals = [part["verdict"] for part in components.values()]
    if "NOT_VERIFIED" in vals:
        overall = "NOT_VERIFIED"
    elif all(v == "VERIFIED" for v in vals):
        overall = "VERIFIED"
    else:
        overall = "UNKNOWN"
    report: dict[str, Any] = {
        "schema_version": "sable.x402.closure-report.v1",
        "tool_version": VERSION,
        "case_id": case.get("case_id", "unnamed-case"),
        "audited_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "offline_evidence_dossier_audit",
        "overall_verdict": overall,
        "components": components,
        "expected": expected,
        "source_dossier_claims": case.get("source_dossier_claims", []),
        "limitations": [
            "This tool audits supplied evidence; it does not fetch or independently authenticate source websites.",
            "A settlement transaction does not, by itself, establish semantic correctness or delivery of a paid response.",
            "A metadata match is not an authoritative response receipt or downstream state readback.",
            "A SHA-256 digest proves byte consistency only when the digest itself is anchored to a trusted receipt; it does not prove source authenticity.",
            "No payment was submitted and no paid endpoint was called by this tool.",
        ],
    }
    report["report_sha256"] = _hash_json(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Evidence dossier JSON")
    parser.add_argument("--output", help="Write report JSON to this path; default is stdout")
    args = parser.parse_args(argv)
    try:
        case = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = assess(case)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"sable_x402_closure: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["overall_verdict"] == "VERIFIED" else 1 if report["overall_verdict"] == "NOT_VERIFIED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
