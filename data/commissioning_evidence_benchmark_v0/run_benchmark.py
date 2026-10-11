#!/usr/bin/env python3
"""Run authored graph mutations against the SABLE local-only graph validator."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sable_commissioning_evidence_graph import validate_graph  # noqa: E402

CASES = Path(__file__).with_name("cases.json")
BASE = ROOT / "examples" / "commissioning-evidence-graph.synthetic.json"

def apply_mutation(graph, mutation):
    op = mutation["op"]
    if op == "none":
        return
    if op in {"set_node_field", "unset_node_field"}:
        node = next(n for n in graph["nodes"] if n["id"] == mutation["node_id"])
        if op == "set_node_field":
            node[mutation["field"]] = mutation["value"]
        else:
            node.pop(mutation["field"], None)
        return
    if op == "remove_edge":
        graph["edges"] = [e for e in graph["edges"] if not (
            e["source"] == mutation["source"] and
            e["relation"] == mutation["relation"] and
            e["target"] == mutation["target"]
        )]
        return
    if op == "add_unlinked_asset_and_repoint_test":
        node_id = mutation["node_id"]
        graph["nodes"].append({"id": node_id, "kind": "asset", "label": "Synthetic out-of-package asset"})
        for edge in graph["edges"]:
            if edge["source"] == "FPT-AHU-01" and edge["relation"] == "tests_asset":
                edge["target"] = node_id
                return
        raise ValueError("base fixture lacks tests_asset edge")
    raise ValueError("unsupported mutation operation: " + str(op))

def run():
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    base = json.loads(BASE.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        graph = copy.deepcopy(base)
        apply_mutation(graph, case["mutation"])
        receipt = validate_graph(graph, evidence_root=ROOT)
        codes = {finding["code"] for finding in receipt["findings"]}
        expected_code = case["expected_finding_code"]
        ok = receipt["verdict"] == case["expected_verdict"] and (
            expected_code is None or expected_code in codes
        )
        results.append({
            "case_id": case["case_id"],
            "name": case["name"],
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": receipt["verdict"],
            "expected_finding_code": expected_code,
            "finding_codes": sorted(codes),
            "pass": ok,
            "requirement_ids": case["requirement_ids"],
        })
    output = {
        "benchmark_id": "SABLE-CX-EVIDENCE-GAP-BENCHMARK",
        "version": "0.1.0",
        "case_count": len(results),
        "passed": sum(1 for item in results if item["pass"]),
        "failed": sum(1 for item in results if not item["pass"]),
        "qualification": "Synthetic mutations only. No customer data, operational precision/recall, safety assurance, or acceptance certification is established.",
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if output["failed"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(run())
