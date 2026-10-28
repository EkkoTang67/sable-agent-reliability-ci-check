#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "swarm_runtime.py"
SPEC = importlib.util.spec_from_file_location("swarm_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
swarm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(swarm)


class SwarmRuntimeTests(unittest.TestCase):
    def test_registers_ten_thousand_distinct_agent_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = swarm.connect(Path(tmp) / "state.db")
            try:
                stats = swarm.initialize(conn, 10_000)
                self.assertEqual(sum(stats.values()), 10_000)
                self.assertEqual(stats["prototype_cash"], 4_500)
                self.assertEqual(stats["niche_pain"], 4_500)
                self.assertEqual(stats["audit"], 1_000)
                self.assertEqual(conn.execute("SELECT COUNT(DISTINCT agent_id) FROM agents").fetchone()[0], 10_000)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM agents WHERE state='IDLE'").fetchone()[0], 10_000)
            finally:
                conn.close()

    def test_enqueue_requires_supported_mode_and_deduplicates_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            infile = root / "in.jsonl"
            infile.write_text(json.dumps({"candidate_id":"x","mode":"niche_pain","source_url":"https://example.com"})+"\n", encoding="utf-8")
            conn = swarm.connect(root / "state.db")
            try:
                self.assertEqual(swarm.enqueue_file(conn, infile), 1)
                self.assertEqual(swarm.enqueue_file(conn, infile), 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 1)
            finally:
                conn.close()

    def test_status_reports_idle_agents_and_queued_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = swarm.connect(Path(tmp) / "state.db")
            try:
                swarm.initialize(conn, 100)
                self.assertEqual(swarm.show_status(conn)["agents_by_state"], {"IDLE": 100})
            finally:
                conn.close()

    def test_scouts_are_distinct_from_auditors(self):
        self.assertIn("counterevidence", swarm.prompt_for("commercial_reality_auditor"))
        self.assertIn("economic consequence", swarm.prompt_for("niche_pain_scout"))
        self.assertIn("acceptance_test", swarm.prompt_for("prototype_cash_scout"))

    def test_real_orchestration_pipeline_uses_distinct_scout_and_auditor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "state.db"
            candidates = root / "candidates.jsonl"
            candidates.write_text(json.dumps({
                "candidate_id": "candidate-1", "mode": "niche_pain",
                "source_url": "https://example.com/public-issue",
                "upfront_cost": 0, "payer_role": "operations lead",
                "pain_statement": "manual exception handling",
                "economic_consequence": "repeat rework",
                "evidence_url": "https://example.com/public-issue",
                "buyer_action": "none",
            }) + "\n", encoding="utf-8")
            conn = swarm.connect(db)
            try:
                swarm.initialize(conn, 100)
                swarm.enqueue_file(conn, candidates)
            finally:
                conn.close()
            outputs = [
                json.dumps({"pain_hypothesis":"exception triage", "unknowns":["frequency"]}),
                json.dumps({"verdict":"HOLD", "critical_unknowns":["payer interview not collected"]}),
            ]
            with patch.object(swarm, "call_model", side_effect=outputs) as mocked:
                result = swarm.run_one(db, "candidate-1", "http://127.0.0.1:11434/v1", "unit-test-model", None)
            self.assertEqual(mocked.call_count, 2)
            self.assertNotEqual(result["scout_agent_id"], result["auditor_agent_id"])
            scout_payload = mocked.call_args_list[0].args[4]
            audit_payload = mocked.call_args_list[1].args[4]
            self.assertEqual(scout_payload["agent_profile"]["agent_id"], result["scout_agent_id"])
            self.assertTrue(scout_payload["agent_profile"]["domain_focus"])
            self.assertEqual(audit_payload["auditor_profile"]["agent_id"], result["auditor_agent_id"])
            self.assertFalse(result["cash_received"])
            conn = swarm.connect(db)
            try:
                task = conn.execute("SELECT state FROM tasks WHERE task_id='candidate-1'").fetchone()
                self.assertEqual(task["state"], "REVIEW_REQUIRED")
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM agents WHERE state='BUSY'").fetchone()[0], 0)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM events WHERE task_id='candidate-1'").fetchone()[0], 2)
            finally:
                conn.close()

    def test_run_rejects_missing_model_before_calls(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(StringIO()):
            rc = swarm.main(["run", "--db", str(Path(tmp) / "state.db")])
            self.assertEqual(rc, 2)

    def test_remote_model_endpoint_requires_explicit_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(StringIO()):
            rc = swarm.main(["run", "--db", str(Path(tmp) / "state.db"), "--model", "test-model",
                             "--base-url", "https://api.example.com/v1"])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
