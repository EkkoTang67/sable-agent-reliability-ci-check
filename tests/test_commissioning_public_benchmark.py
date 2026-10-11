import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "data" / "commissioning_evidence_benchmark_v0" / "run_benchmark.py"
SPEC = importlib.util.spec_from_file_location("sable_public_benchmark", SCRIPT)
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)

class PublicCommissioningBenchmarkTests(unittest.TestCase):
    def test_all_authored_mutation_cases_match_expected_labels(self):
        cases = json.loads((SCRIPT.parent / "cases.json").read_text(encoding="utf-8"))["cases"]
        base = json.loads((ROOT / "examples" / "commissioning-evidence-graph.synthetic.json").read_text(encoding="utf-8"))
        import copy
        from sable_commissioning_evidence_graph import validate_graph
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                graph = copy.deepcopy(base)
                BENCHMARK.apply_mutation(graph, case["mutation"])
                receipt = validate_graph(graph, ROOT)
                codes = {f["code"] for f in receipt["findings"]}
                self.assertEqual(receipt["verdict"], case["expected_verdict"])
                if case["expected_finding_code"]:
                    self.assertIn(case["expected_finding_code"], codes)

    def test_source_profile_has_provenance_and_project_tailoring_guardrail(self):
        profile_path = ROOT / "data" / "commissioning_public_requirements" / "ufgs_01_91_00_15_source_profile.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertTrue(profile["not_customer_operational_data"])
        self.assertIn("actual project", profile["source"]["applicability_warning"].lower())
        self.assertTrue(any(r["requirement_id"] == "UFGS-CX-READINESS-001" for r in profile["requirements"]))
        self.assertTrue(all(r.get("source") is None or isinstance(r.get("source"), str) for r in profile["requirements"]))

if __name__ == "__main__":
    unittest.main()
