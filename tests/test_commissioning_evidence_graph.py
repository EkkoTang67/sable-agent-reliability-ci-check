import copy
import json
import unittest
from pathlib import Path
from sable_commissioning_evidence_graph import validate_graph

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "commissioning-evidence-graph.synthetic.json"

class CommissioningEvidenceGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_complete_synthetic_graph_is_verified(self):
        r = validate_graph(copy.deepcopy(self.graph), ROOT)
        self.assertEqual(r["verdict"], "VERIFIED")
        self.assertEqual(r["summary"]["gaps"], 0)
        self.assertEqual(r["summary"]["critical"], 0)
        self.assertEqual(r["summary"]["locally_hash_verified_sources"], 7)

    def test_hash_mismatch_is_not_verified(self):
        g = copy.deepcopy(self.graph)
        next(n for n in g["nodes"] if n["id"] == "TR-1001")["sha256"] = "0" * 64
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "NOT_VERIFIED")
        self.assertIn("SHA256_MISMATCH", {f["code"] for f in r["findings"]})

    def test_failed_test_is_not_verified(self):
        g = copy.deepcopy(self.graph)
        next(n for n in g["nodes"] if n["id"] == "TR-1001")["outcome"] = "FAIL"
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "NOT_VERIFIED")
        self.assertIn("TEST_FAILED", {f["code"] for f in r["findings"]})
        self.assertIn("SOURCE_FIELD_MISMATCH", {f["code"] for f in r["findings"]})

    def test_unapproved_drawing_is_not_verified(self):
        g = copy.deepcopy(self.graph)
        next(n for n in g["nodes"] if n["id"] == "M-101-C")["approved"] = False
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "NOT_VERIFIED")
        self.assertIn("DOCUMENT_GATE_FAILED", {f["code"] for f in r["findings"]})

    def test_missing_result_link_is_unknown(self):
        g = copy.deepcopy(self.graph)
        g["edges"] = [e for e in g["edges"] if not (e["source"] == "FPT-AHU-01" and e["relation"] == "has_result")]
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "UNKNOWN")
        self.assertIn("TEST_RESULT_MISSING", {f["code"] for f in r["findings"]})

    def test_open_deficiency_is_not_verified(self):
        g = copy.deepcopy(self.graph)
        next(n for n in g["nodes"] if n["id"] == "DEF-04")["status"] = "open"
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "NOT_VERIFIED")
        self.assertIn("DEFICIENCY_NOT_CLOSED", {f["code"] for f in r["findings"]})

    def test_missing_witness_is_unknown_when_required(self):
        g = copy.deepcopy(self.graph)
        g["edges"] = [e for e in g["edges"] if not (e["source"] == "WS-01" and e["relation"] == "witnesses")]
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "UNKNOWN")
        self.assertIn("WITNESS_MISSING", {f["code"] for f in r["findings"]})

    def test_retest_time_reversal_is_not_verified(self):
        g = copy.deepcopy(self.graph)
        next(n for n in g["nodes"] if n["id"] == "RT-04")["observed_at"] = "2026-10-11T08:00:00Z"
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "NOT_VERIFIED")
        self.assertIn("RETEST_TIME_REVERSAL", {f["code"] for f in r["findings"]})

    def test_unsafe_source_path_is_unknown(self):
        g = copy.deepcopy(self.graph)
        next(n for n in g["nodes"] if n["id"] == "WS-01")["source_ref"] = "../../outside.txt"
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "UNKNOWN")
        self.assertIn("UNSAFE_SOURCE_REFERENCE", {f["code"] for f in r["findings"]})

    def test_duplicate_node_id_is_not_verified(self):
        g = copy.deepcopy(self.graph)
        g["nodes"].append(copy.deepcopy(g["nodes"][0]))
        r = validate_graph(g, ROOT)
        self.assertEqual(r["verdict"], "NOT_VERIFIED")
        self.assertIn("DUPLICATE_NODE_ID", {f["code"] for f in r["findings"]})

if __name__ == "__main__":
    unittest.main()
