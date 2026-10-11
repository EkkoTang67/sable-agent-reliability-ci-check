#!/usr/bin/env python3
"""Read-only validator for commissioning evidence graphs.

Validates declared relationships, evidence-file digests, version gates,
deficiency closure, retest ordering, and witness linkage. It does not control
or certify a facility, authenticate human signatures, or query external systems.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
NODE_KINDS = {"asset", "drawing", "procedure", "test", "test_result", "deficiency",
              "corrective_action", "retest", "witness", "turnover_package"}
RELATIONS = {"contains_asset", "contains_evidence", "tests_asset", "uses_drawing",
             "uses_procedure", "has_result", "evidence_for", "corrected_by",
             "retests", "follows_result", "witnesses"}
EVIDENCE_KINDS = {"drawing", "procedure", "test_result", "deficiency",
                  "corrective_action", "retest", "witness"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None

def _receipt(verdict: str, findings: list[dict[str, str]],
             verified_sources: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema": "sable.commissioning-evidence-graph-receipt.v1",
        "validator_version": VERSION,
        "verdict": verdict,
        "scope": "local-file digest and graph-relationship checks only",
        "summary": {
            "findings": len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "gaps": sum(1 for f in findings if f["severity"] == "gap"),
            "locally_hash_verified_sources": len(verified_sources),
        },
        "verified_sources": verified_sources,
        "findings": findings,
        "limitations": [
            "A digest match proves byte identity against the supplied digest, not authorship, accuracy, approval authority, or signature authenticity.",
            "VERIFIED means only that this validator's declared v1 structural gates passed for the supplied local files.",
            "No BMS, EPMS, SCADA, PLC, facility network, control command, external system, or live equipment is accessed.",
            "This output is not a safety certification, engineering opinion, commissioning sign-off, or permission to energize equipment.",
        ],
    }

def validate_graph(document: Any, evidence_root: str | Path | None = None) -> dict[str, Any]:
    """Return a deterministic, evidence-bounded verdict and machine-readable findings."""
    findings: list[dict[str, str]] = []
    verified_sources: list[dict[str, str]] = []
    root = Path(evidence_root or Path.cwd()).resolve()

    def add(severity: str, code: str, message: str, node_id: str = "") -> None:
        item = {"severity": severity, "code": code, "message": message}
        if node_id:
            item["node_id"] = node_id
        findings.append(item)

    if not isinstance(document, dict):
        add("critical", "INVALID_DOCUMENT", "Top-level input must be a JSON object.")
        return _receipt("NOT_VERIFIED", findings, verified_sources)
    nodes_in, edges_in = document.get("nodes"), document.get("edges")
    if not isinstance(nodes_in, list) or not isinstance(edges_in, list):
        add("critical", "INVALID_GRAPH_SHAPE", "nodes and edges must both be arrays.")
        return _receipt("NOT_VERIFIED", findings, verified_sources)

    nodes: dict[str, dict[str, Any]] = {}
    for item in nodes_in:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            add("critical", "INVALID_NODE", "Every node must have a non-empty string id.")
            continue
        nid = item["id"]
        if nid in nodes:
            add("critical", "DUPLICATE_NODE_ID", "Node IDs must be unique.", nid)
            continue
        if item.get("kind") not in NODE_KINDS:
            add("critical", "UNKNOWN_NODE_KIND", "Node kind is outside the supported v1 vocabulary.", nid)
        nodes[nid] = item

    edges: list[dict[str, str]] = []
    for item in edges_in:
        if not isinstance(item, dict):
            add("critical", "INVALID_EDGE", "Every edge must be an object.")
            continue
        source, relation, target = item.get("source"), item.get("relation"), item.get("target")
        if not all(isinstance(x, str) and x for x in (source, relation, target)):
            add("critical", "INVALID_EDGE", "Every edge requires source, relation, and target strings.")
            continue
        if relation not in RELATIONS:
            add("critical", "UNKNOWN_RELATION", "Relation is outside the supported v1 vocabulary.", source)
        if source not in nodes or target not in nodes:
            add("critical", "DANGLING_EDGE", "Edge endpoint does not exist: " + source + " -> " + target, source)
        edges.append({"source": source, "relation": relation, "target": target})

    def related(source: str, relation: str, target_kind: str | None = None) -> list[dict[str, Any]]:
        result = []
        for edge in edges:
            if edge["source"] != source or edge["relation"] != relation:
                continue
            target = nodes.get(edge["target"])
            if target and (target_kind is None or target.get("kind") == target_kind):
                result.append(target)
        return result

    # Local-only hashing. Do not follow URLs, network shares, or paths escaping root.
    for nid, node in nodes.items():
        if node.get("kind") not in EVIDENCE_KINDS:
            continue
        source_ref, expected = node.get("source_ref"), node.get("sha256")
        if not isinstance(source_ref, str) or not source_ref:
            add("gap", "SOURCE_REFERENCE_MISSING", "Evidence node has no local source_ref.", nid)
            continue
        if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            add("gap", "SHA256_MISSING_OR_INVALID", "Evidence node needs a 64-character SHA-256 digest.", nid)
            continue
        rel = Path(source_ref)
        if rel.is_absolute() or ".." in rel.parts or source_ref.startswith(("http://", "https://", "file://")):
            add("gap", "UNSAFE_SOURCE_REFERENCE", "Only relative local evidence paths inside the evidence root are allowed.", nid)
            continue
        try:
            path = (root / rel).resolve(strict=True)
            if not path.is_relative_to(root) or not path.is_file():
                add("gap", "SOURCE_OUTSIDE_ROOT", "Evidence source is not a regular file inside the evidence root.", nid)
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, RuntimeError, ValueError):
            add("gap", "SOURCE_UNAVAILABLE", "Evidence source could not be read locally; no network fallback is attempted.", nid)
            continue
        if actual.lower() != expected.lower():
            add("critical", "SHA256_MISMATCH", "Local evidence bytes do not match the declared SHA-256 digest.", nid)
            continue
        verified_sources.append({"node_id": nid, "source_ref": source_ref, "sha256": actual})

    packages = [n for n in nodes.values() if n.get("kind") == "turnover_package"]
    if not packages:
        add("gap", "TURNOVER_PACKAGE_MISSING", "Graph has no turnover_package root.")
    for package in packages:
        pid = package["id"]
        assets = related(pid, "contains_asset", "asset")
        if not assets:
            add("gap", "PACKAGE_HAS_NO_ASSET", "Turnover package is not linked to an asset.", pid)
        tests = related(pid, "contains_evidence", "test")
        if not tests:
            add("gap", "PACKAGE_HAS_NO_TESTS", "Turnover package contains no linked test records.", pid)

        for test in tests:
            tid = test["id"]
            test_assets = related(tid, "tests_asset", "asset")
            drawings = related(tid, "uses_drawing", "drawing")
            procedures = related(tid, "uses_procedure", "procedure")
            results = related(tid, "has_result", "test_result")
            if not test_assets:
                add("gap", "TEST_ASSET_LINK_MISSING", "Test is not linked to an asset.", tid)
            elif assets and not any(a["id"] in {x["id"] for x in assets} for a in test_assets):
                add("critical", "TEST_ASSET_MISMATCH", "Test asset is not part of this turnover package.", tid)
            if not drawings:
                add("gap", "DRAWING_LINK_MISSING", "Test has no linked governing drawing.", tid)
            if not procedures:
                add("gap", "PROCEDURE_LINK_MISSING", "Test has no linked governing procedure.", tid)
            if not results:
                add("gap", "TEST_RESULT_MISSING", "Test has no linked result.", tid)

            for governing_doc in drawings + procedures:
                did = governing_doc["id"]
                for flag in ("approved", "current"):
                    if governing_doc.get(flag) is False:
                        add("critical", "DOCUMENT_GATE_FAILED", flag + " must be true for the governing document.", did)
                    elif governing_doc.get(flag) is not True:
                        add("gap", "DOCUMENT_GATE_UNKNOWN", flag + " state is not explicitly true.", did)

            for result in results:
                rid = result["id"]
                if not any(t["id"] == tid for t in related(rid, "evidence_for", "test")):
                    add("gap", "RESULT_TEST_LINK_MISSING", "Result does not point back to its test via evidence_for.", rid)
                outcome = str(result.get("outcome", "")).upper()
                if outcome == "FAIL":
                    add("critical", "TEST_FAILED", "Test result outcome is FAIL.", rid)
                elif outcome != "PASS":
                    add("gap", "TEST_OUTCOME_UNKNOWN", "Test outcome is missing or not PASS/FAIL.", rid)
                if _parse_time(result.get("observed_at")) is None:
                    add("gap", "RESULT_TIME_UNKNOWN", "Test result needs a timezone-aware observed_at timestamp.", rid)
                requirements = document.get("requirements", {})
                if isinstance(requirements, dict) and requirements.get("witness_required") is True:
                    witnesses = related(rid, "witnesses", "witness")
                    if not witnesses:
                        add("gap", "WITNESS_MISSING", "Package requires a witness record for each test result.", rid)
                    for witness in witnesses:
                        if witness.get("signed") is False:
                            add("critical", "WITNESS_NOT_SIGNED", "Witness record is explicitly not signed.", witness["id"])
                        elif witness.get("signed") is not True:
                            add("gap", "WITNESS_SIGNATURE_UNKNOWN", "Witness signature state is not explicitly true.", witness["id"])

        deficiencies = [n for n in nodes.values() if n.get("kind") == "deficiency" and
                        any(e["source"] == pid and e["relation"] == "contains_evidence" and e["target"] == n["id"] for e in edges)]
        for deficiency in deficiencies:
            did = deficiency["id"]
            status = str(deficiency.get("status", "")).lower()
            if status in {"open", "in_progress", "reopened"}:
                add("critical", "DEFICIENCY_NOT_CLOSED", "Deficiency remains open, in progress, or reopened.", did)
            elif status not in {"closed", "resolved"}:
                add("gap", "DEFICIENCY_STATUS_UNKNOWN", "Deficiency closure state is not explicitly closed/resolved.", did)
            actions = related(did, "corrected_by", "corrective_action")
            retests = [n for n in nodes.values() if n.get("kind") == "retest" and
                       any(e["source"] == n["id"] and e["relation"] == "retests" and e["target"] == did for e in edges)]
            if not actions:
                add("gap", "CORRECTIVE_ACTION_LINK_MISSING", "Deficiency has no linked corrective action.", did)
            for action in actions:
                if str(action.get("status", "")).lower() != "completed":
                    severity = "critical" if action.get("status") else "gap"
                    add(severity, "CORRECTIVE_ACTION_NOT_COMPLETE", "Corrective action must be explicitly marked completed.", action["id"])
            if not retests:
                add("gap", "RETEST_MISSING", "Deficiency has no linked retest evidence.", did)
            for retest in retests:
                rid = retest["id"]
                outcome = str(retest.get("outcome", "")).upper()
                if outcome == "FAIL":
                    add("critical", "RETEST_FAILED", "Retest outcome is FAIL.", rid)
                elif outcome != "PASS":
                    add("gap", "RETEST_OUTCOME_UNKNOWN", "Retest outcome is missing or not PASS.", rid)
                prior_results = related(rid, "follows_result", "test_result")
                if not prior_results:
                    add("gap", "RETEST_PRIOR_RESULT_MISSING", "Retest does not identify the result it follows.", rid)
                rt = _parse_time(retest.get("observed_at"))
                for prior in prior_results:
                    pt = _parse_time(prior.get("observed_at"))
                    if rt is None or pt is None:
                        add("gap", "RETEST_ORDER_UNKNOWN", "Retest and prior result need timezone-aware timestamps.", rid)
                    elif rt < pt:
                        add("critical", "RETEST_TIME_REVERSAL", "Retest timestamp precedes its prior result.", rid)

    verdict = "NOT_VERIFIED" if any(f["severity"] == "critical" for f in findings) else (
        "UNKNOWN" if any(f["severity"] == "gap" for f in findings) else "VERIFIED")
    return _receipt(verdict, findings, verified_sources)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a commissioning evidence graph without connecting to facility systems.")
    parser.add_argument("--file", required=True, help="Path to graph JSON.")
    parser.add_argument("--root", default=".", help="Root directory containing local evidence files (default: current directory).")
    parser.add_argument("--out", help="Optional JSON receipt output path; receipt also prints to stdout.")
    args = parser.parse_args(argv)
    try:
        graph = json.loads(Path(args.file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "NOT_VERIFIED", "error": str(exc)}, indent=2))
        return 1
    receipt = validate_graph(graph, evidence_root=args.root)
    rendered = json.dumps(receipt, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if receipt["verdict"] == "VERIFIED" else (1 if receipt["verdict"] == "NOT_VERIFIED" else 2)

if __name__ == "__main__":
    sys.exit(main())
