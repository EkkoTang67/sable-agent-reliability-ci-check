from __future__ import annotations

import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from authorization_harness import AuthorizationHarness


class FakeClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            return self.value

    def advance(self, seconds: int) -> None:
        with self.lock:
            self.value += timedelta(seconds=seconds)


class AuthorizationHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.clock = FakeClock()
        self.harness = AuthorizationHarness(Path(self.temp_dir.name) / "test.sqlite3", self.clock)
        self.action = {
            "actor_id": "agent:ap-01",
            "operation": "payment.release",
            "resource_id": "invoice:INV-1",
            "parameters": {
                "amount_minor": 125000,
                "currency": "USD",
                "beneficiary_id": "supplier:SUP-7",
            },
        }
        self.executions: list[dict] = []
        self.execution_lock = threading.Lock()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def issue(self, ttl_seconds: int = 60) -> dict[str, str]:
        return self.harness.issue_approval(
            actor_id=self.action["actor_id"],
            operation=self.action["operation"],
            resource_id=self.action["resource_id"],
            parameters=self.action["parameters"],
            approved_by="human:approver-01",
            ttl_seconds=ttl_seconds,
        )

    def executor(self, action: dict) -> dict:
        with self.execution_lock:
            self.executions.append(action)
            return {"sandbox_receipt_id": f"SIM-{len(self.executions):04d}"}

    def execute(self, approval: dict, **overrides) -> dict:
        arguments = {
            "token": approval["token"],
            **self.action,
            "executor": self.executor,
        }
        arguments.update(overrides)
        return self.harness.execute(**arguments)

    def test_exact_scope_executes_once_and_replay_is_denied(self) -> None:
        approval = self.issue()
        first = self.execute(approval)
        second = self.execute(approval)
        self.assertEqual(first["verdict"], "AUTHORIZED_SANDBOX_EXECUTED")
        self.assertEqual(second["verdict"], "DENIED")
        self.assertEqual(second["reason"], "APPROVAL_ALREADY_CONSUMED")
        self.assertEqual(len(self.executions), 1)

    def test_parameter_tampering_is_denied_without_consuming_approval(self) -> None:
        approval = self.issue()
        changed = dict(self.action["parameters"], beneficiary_id="supplier:ATTACKER")
        denied = self.execute(approval, parameters=changed)
        allowed = self.execute(approval)
        self.assertEqual(denied["reason"], "SCOPE_MISMATCH")
        self.assertEqual(allowed["verdict"], "AUTHORIZED_SANDBOX_EXECUTED")
        self.assertEqual(len(self.executions), 1)

    def test_actor_mismatch_is_denied_without_consuming_approval(self) -> None:
        approval = self.issue()
        denied = self.execute(approval, actor_id="agent:other-user")
        allowed = self.execute(approval)
        self.assertEqual(denied["reason"], "ACTOR_MISMATCH")
        self.assertEqual(allowed["verdict"], "AUTHORIZED_SANDBOX_EXECUTED")

    def test_expired_approval_is_denied(self) -> None:
        approval = self.issue(ttl_seconds=2)
        self.clock.advance(3)
        result = self.execute(approval)
        self.assertEqual(result["verdict"], "DENIED")
        self.assertEqual(result["reason"], "APPROVAL_EXPIRED")
        self.assertEqual(len(self.executions), 0)

    def test_concurrent_replay_allows_exactly_one_consumer(self) -> None:
        approval = self.issue()
        barrier = threading.Barrier(12)

        def worker() -> dict:
            barrier.wait(timeout=10)
            return self.execute(approval)

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: worker(), range(12)))

        allowed = [r for r in results if r["verdict"] == "AUTHORIZED_SANDBOX_EXECUTED"]
        denied = [r for r in results if r["verdict"] == "DENIED"]
        self.assertEqual(len(allowed), 1)
        self.assertEqual(len(denied), 11)
        self.assertEqual(len(self.executions), 1)

    def test_approval_token_is_not_stored_in_plaintext(self) -> None:
        approval = self.issue()
        connection = self.harness._connect()
        try:
            rows = connection.execute("SELECT token_hash FROM approvals").fetchall()
        finally:
            connection.close()
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]["token_hash"], approval["token"])
        self.assertEqual(len(rows[0]["token_hash"]), 64)

    def test_audit_chain_verifies_and_rejects_mutation(self) -> None:
        approval = self.issue()
        self.execute(approval)
        chain = self.harness.verify_audit_chain()
        self.assertTrue(chain["valid"])
        self.assertGreaterEqual(chain["checked_events"], 3)
        connection = self.harness._connect()
        try:
            with self.assertRaises(Exception):
                connection.execute("UPDATE audit_events SET event_json = '{}' WHERE event_id = 1")
        finally:
            connection.close()

    def test_operation_and_resource_are_bound_to_approval(self) -> None:
        approval = self.issue()
        wrong_operation = self.execute(approval, operation="vendor.account.change")
        wrong_resource = self.execute(approval, resource_id="invoice:INV-OTHER")
        correct = self.execute(approval)
        self.assertEqual(wrong_operation["reason"], "SCOPE_MISMATCH")
        self.assertEqual(wrong_resource["reason"], "SCOPE_MISMATCH")
        self.assertEqual(correct["verdict"], "AUTHORIZED_SANDBOX_EXECUTED")

    def test_executor_failure_does_not_reopen_consumed_approval(self) -> None:
        approval = self.issue()

        def failing_executor(_action: dict) -> dict:
            raise RuntimeError("synthetic failure")

        failed = self.execute(approval, executor=failing_executor)
        replay = self.execute(approval)
        self.assertEqual(failed["verdict"], "AUTHORIZED_EXECUTION_FAILED")
        self.assertEqual(replay["reason"], "APPROVAL_ALREADY_CONSUMED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
