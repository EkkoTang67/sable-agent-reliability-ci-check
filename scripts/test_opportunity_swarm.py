#!/usr/bin/env python3
"""Standard-library regression tests for opportunity_swarm.py."""
import unittest
from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).with_name("opportunity_swarm.py")
SPEC = importlib.util.spec_from_file_location("opportunity_swarm", MODULE_PATH)
assert SPEC and SPEC.loader
swarm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(swarm)


class SwarmTests(unittest.TestCase):
    def test_manifest_creates_dormant_10000_slots_evenly_split(self):
        rows = list(swarm.build_manifest(10_000))
        self.assertEqual(len(rows), 10_000)
        self.assertEqual(sum(r["mode"] == "prototype_cash" for r in rows), 5_000)
        self.assertEqual(sum(r["mode"] == "niche_pain" for r in rows), 5_000)
        self.assertTrue(all(r["status"] == "DORMANT" for r in rows))
        self.assertTrue(all(r["llm_calls"] == 0 and r["cash_budget"] == 0 for r in rows))
        self.assertEqual(len({r["pair_id"] for r in rows}), 10_000)

    def cash_candidate(self):
        return {
            "candidate_id": "cash-1",
            "mode": "prototype_cash",
            "source_url": "https://example.com/task",
            "task_open": True,
            "upfront_cost": 0,
            "reward_amount": 25,
            "reward_currency": "USD",
            "acceptance_criteria": ["test"],
            "funding_status": "confirmed",
            "payout_method_confirmed": True,
            "mainland_china_eligible": True,
        }

    def test_cash_candidate_passes_only_when_all_gates_pass(self):
        self.assertEqual(swarm.screen_record(self.cash_candidate())["decision"],
                         "READY_FOR_SCOPED_ATTEMPT")

    def test_positive_upfront_cost_is_rejected(self):
        candidate = self.cash_candidate()
        candidate["upfront_cost"] = 1
        result = swarm.screen_record(candidate)
        self.assertEqual(result["decision"], "REJECT")
        self.assertFalse(result["cash_received"])

    def test_unknown_cost_stays_on_hold(self):
        candidate = self.cash_candidate()
        del candidate["upfront_cost"]
        self.assertEqual(swarm.screen_record(candidate)["decision"], "HOLD")

    def test_unconfirmed_payout_stays_on_hold(self):
        candidate = self.cash_candidate()
        candidate["payout_method_confirmed"] = False
        self.assertEqual(swarm.screen_record(candidate)["decision"], "HOLD")

    def test_crypto_points_do_not_pass_as_cash(self):
        candidate = self.cash_candidate()
        candidate["reward_currency"] = "USDC"
        self.assertEqual(swarm.screen_record(candidate)["decision"], "HOLD")

    def test_pain_without_buyer_action_only_reaches_payer_validation(self):
        result = swarm.screen_record({
            "candidate_id": "pain-1", "mode": "niche_pain",
            "source_url": "https://example.com/post",
            "upfront_cost": 0,
            "payer_role": "finance manager",
            "pain_statement": "manual invoice rework",
            "economic_consequence": "hours lost weekly",
            "evidence_url": "https://example.com/post",
            "buyer_action": "none",
        })
        self.assertEqual(result["decision"], "VALIDATE_PAYER")

    def test_buyer_commitment_unlocks_prototype(self):
        result = swarm.screen_record({
            "candidate_id": "pain-2", "mode": "niche_pain",
            "source_url": "https://example.com/post",
            "upfront_cost": 0,
            "payer_role": "finance manager",
            "pain_statement": "manual invoice rework",
            "economic_consequence": "hours lost weekly",
            "evidence_url": "https://example.com/post",
            "buyer_action": "budgeted_trial",
        })
        self.assertEqual(result["decision"], "READY_FOR_PROTOTYPE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
