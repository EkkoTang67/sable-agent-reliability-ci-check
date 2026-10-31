#!/usr/bin/env python3
"""Run a fully local, no-network transaction authorization demo."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from threading import Lock

from authorization_harness import AuthorizationHarness


ACTION = {
    "actor_id": "agent:ap-demo-01",
    "operation": "payment.release",
    "resource_id": "invoice:INV-2026-1042",
    "parameters": {
        "amount_minor": 125000,
        "currency": "USD",
        "beneficiary_id": "supplier:SUP-007",
    },
}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="tack-demo-") as temp_dir:
        harness = AuthorizationHarness(Path(temp_dir) / "demo.sqlite3")
        approval = harness.issue_approval(
            actor_id=ACTION["actor_id"],
            operation=ACTION["operation"],
            resource_id=ACTION["resource_id"],
            parameters=ACTION["parameters"],
            approved_by="human:approver-01",
            ttl_seconds=300,
        )

        sandbox_executions: list[dict] = []
        lock = Lock()

        def sandbox_executor(action: dict) -> dict:
            with lock:
                sandbox_executions.append(action)
                return {"sandbox_receipt_id": f"SIM-{len(sandbox_executions):04d}"}

        tampered = dict(ACTION["parameters"], beneficiary_id="supplier:ATTACKER")
        tamper_attempt = harness.execute(
            token=approval["token"],
            actor_id=ACTION["actor_id"],
            operation=ACTION["operation"],
            resource_id=ACTION["resource_id"],
            parameters=tampered,
            executor=sandbox_executor,
        )
        valid_attempt = harness.execute(
            token=approval["token"],
            actor_id=ACTION["actor_id"],
            operation=ACTION["operation"],
            resource_id=ACTION["resource_id"],
            parameters=ACTION["parameters"],
            executor=sandbox_executor,
        )
        replay_attempt = harness.execute(
            token=approval["token"],
            actor_id=ACTION["actor_id"],
            operation=ACTION["operation"],
            resource_id=ACTION["resource_id"],
            parameters=ACTION["parameters"],
            executor=sandbox_executor,
        )

        report = {
            "demo_mode": "LOCAL_SANDBOX_ONLY",
            "external_network_used": False,
            "real_payment_or_external_side_effect": False,
            "action_scope": {
                "actor_id": ACTION["actor_id"],
                "operation": ACTION["operation"],
                "resource_id": ACTION["resource_id"],
                "parameters": ACTION["parameters"],
            },
            "attempts": {
                "parameter_tampering": tamper_attempt,
                "approved_action": valid_attempt,
                "replay": replay_attempt,
            },
            "sandbox_execution_count": len(sandbox_executions),
            "audit_chain": harness.verify_audit_chain(),
            "audit_events": harness.get_audit_events(),
            "limitations": [
                "The demo does not authenticate the human approver; approval issuance is assumed to be called by a trusted approval system.",
                "The database coordinates one local SQLite instance only; it is not a distributed or high-availability lock.",
                "One-time approval consumption does not guarantee exactly-once external execution. Production adapters need downstream idempotency and reconciliation.",
                "All identities, invoice data, approvals, and execution receipts are synthetic.",
            ],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
