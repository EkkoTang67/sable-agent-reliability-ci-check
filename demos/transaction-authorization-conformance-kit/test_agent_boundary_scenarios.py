from __future__ import annotations

import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from authorization_harness import (
    AuthorizationHarness,
    classify_independent_observation,
)


class FakeClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            return self.value

    def advance(self, seconds: int) -> None:
        with self.lock:
            self.value += timedelta(seconds=seconds)


class AgentBoundaryScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "boundary.sqlite3"
        self.clock = FakeClock()
        self.harness = AuthorizationHarness(self.db_path, self.clock)
        self.action = {
            "actor_id": "agent:ap-01",
            "operation": "payment.release",
            "resource_id": "invoice:INV-8",
            "parameters": {
                "amount_minor": 88000,
                "currency": "USD",
                "beneficiary_id": "supplier:SUP-8",
            },
        }
        self.effects: list[dict] = []
        self.effect_lock = threading.Lock()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def issue(self, ttl_seconds: int = 60) -> dict[str, str]:
        return self.harness.issue_approval(
            **self.action,
            approved_by="human:approver-8",
            ttl_seconds=ttl_seconds,
        )

    def executor(self, action: dict) -> dict:
        with self.effect_lock:
            self.effects.append(action)
            return {"sandbox_receipt_id": f"SIM-{len(self.effects):04d}"}

    def execute(self, token: str = "", **overrides) -> dict:
        args = {"token": token, **self.action, "executor": self.executor}
        args.update(overrides)
        return self.harness.execute(**args)

    def test_ab01_explicit_denial_is_audited_and_has_no_effect(self) -> None:
        denial = self.harness.record_denial(
            **self.action,
            denied_by="human:approver-8",
            reason="outside approved spend mandate",
        )
        result = self.execute(token="")
        events = self.harness.get_audit_events()
        self.assertEqual(denial["verdict"], "DENIED")
        self.assertEqual(result["reason"], "APPROVAL_NOT_FOUND")
        self.assertTrue(any(e["event"] == "APPROVAL_DENIED" for e in events))
        self.assertEqual(self.effects, [])

    def test_ab02_approver_unavailable_fails_closed(self) -> None:
        # No approval is issued when the approver is unavailable.
        result = self.execute(token="")
        self.assertEqual(result["verdict"], "DENIED")
        self.assertEqual(result["reason"], "APPROVAL_NOT_FOUND")
        self.assertEqual(self.effects, [])

    def test_ab03_alternate_tool_route_still_requires_same_approval(self) -> None:
        # A second tool adapter is modeled as another route into the same host guard.
        alternate_executor = lambda action: self.effects.append(action)
        result = self.execute(token="", executor=alternate_executor)
        self.assertEqual(result["verdict"], "DENIED")
        self.assertEqual(self.effects, [])

    def test_ab04_guard_storage_unavailable_prevents_execution(self) -> None:
        self.db_path.unlink()
        self.db_path.mkdir()
        with self.assertRaises(sqlite3.OperationalError):
            self.execute(token="synthetic-token")
        self.assertEqual(self.effects, [])

    def test_ab05_mixed_batch_order_never_bypasses_protected_action(self) -> None:
        for order in (("protected", "read"), ("read", "protected")):
            self.effects.clear()
            for item in order:
                if item == "protected":
                    result = self.execute(token="")
                    self.assertEqual(result["verdict"], "DENIED")
                else:
                    # Read-only operation is explicitly outside the protected write boundary.
                    self.effects.append({"operation": "read-only", "result": "OK"})
            self.assertEqual(
                sum(1 for e in self.effects if e.get("operation") == "payment.release"),
                0,
            )

    def test_ab06_expiry_and_parameter_tampering_are_denied(self) -> None:
        expired = self.issue(ttl_seconds=2)
        self.clock.advance(3)
        expired_result = self.execute(token=expired["token"])

        valid = self.issue()
        changed = dict(self.action["parameters"], amount_minor=990000)
        tamper_result = self.execute(token=valid["token"], parameters=changed)

        self.assertEqual(expired_result["reason"], "APPROVAL_EXPIRED")
        self.assertEqual(tamper_result["reason"], "SCOPE_MISMATCH")
        self.assertEqual(self.effects, [])

    def test_ab07_concurrent_one_time_approval_has_one_effect(self) -> None:
        approval = self.issue()
        barrier = threading.Barrier(12)

        def worker() -> dict:
            barrier.wait(timeout=10)
            return self.execute(token=approval["token"])

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: worker(), range(12)))

        allowed = [r for r in results if r["verdict"] == "AUTHORIZED_SANDBOX_EXECUTED"]
        denied = [r for r in results if r["verdict"] == "DENIED"]
        self.assertEqual(len(allowed), 1)
        self.assertEqual(len(denied), 11)
        self.assertEqual(len(self.effects), 1)

    def test_ab08_claimed_success_without_independent_observation_is_unknown(self) -> None:
        self.assertEqual(classify_independent_observation(True, None), "UNKNOWN")
        self.assertEqual(
            classify_independent_observation(True, {"effect_observed": True}),
            "PASS",
        )
        self.assertEqual(
            classify_independent_observation(True, {"effect_observed": False}),
            "FAIL",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
