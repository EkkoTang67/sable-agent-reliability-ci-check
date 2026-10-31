import json
import unittest
from pathlib import Path

from workbench.evidence_workbench import evaluate_package, render_markdown

ROOT = Path(__file__).resolve().parents[1] / "samples"


class EvidenceWorkbenchTests(unittest.TestCase):
    def load(self, name):
        raw = (ROOT / name).read_bytes()
        return json.loads(raw.decode("utf-8")), raw

    def test_cargo_fixture_has_pass_and_gap(self):
        package, raw = self.load("cargo_claims.synthetic.json")
        report = evaluate_package(package, raw)
        self.assertEqual(report["overall_verdict"], "GAP")
        self.assertEqual([c["verdict"] for c in report["case_reports"]], ["PASS", "GAP"])

    def test_warranty_fixture_preserves_unknown(self):
        package, raw = self.load("equipment_warranty.synthetic.json")
        report = evaluate_package(package, raw)
        self.assertEqual(report["overall_verdict"], "UNKNOWN")
        self.assertEqual([c["verdict"] for c in report["case_reports"]], ["PASS", "UNKNOWN"])

    def test_same_check_detects_conflict(self):
        package, raw = self.load("cargo_claims.synthetic.json")
        result = evaluate_package(package, raw)["case_reports"][1]["checks"][0]
        self.assertEqual(result["status"], "GAP")
        self.assertEqual(result["source_refs"], ["synthetic://cargo/claim-002", "synthetic://cargo/bol-002"])

    def test_missing_record_is_unknown_not_pass(self):
        package, raw = self.load("equipment_warranty.synthetic.json")
        result = evaluate_package(package, raw)["case_reports"][1]["checks"][1]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["missing"][0]["reason"], "record_not_found")

    def test_duplicate_record_ids_rejected(self):
        package, raw = self.load("cargo_claims.synthetic.json")
        package["cases"][0]["records"].append(dict(package["cases"][0]["records"][0]))
        with self.assertRaisesRegex(ValueError, "record_id values"):
            evaluate_package(package, raw)

    def test_unknown_check_type_rejected(self):
        package, raw = self.load("cargo_claims.synthetic.json")
        package["cases"][0]["checks"][0]["type"] = "legal_entitlement"
        with self.assertRaisesRegex(ValueError, "unsupported check type"):
            evaluate_package(package, raw)

    def test_markdown_report_contains_limitations_and_digest(self):
        package, raw = self.load("cargo_claims.synthetic.json")
        report = evaluate_package(package, raw)
        rendered = render_markdown(report)
        self.assertIn("Input SHA-256", rendered)
        self.assertIn("does not authenticate a source", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
