"""Local reference harness for transaction-bound, single-use approvals.

This is a sandbox demonstration, not a production authorization service.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


GENESIS_HASH = "0" * 64
DEFAULT_POLICY_VERSION = "demo-policy-v1"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _action_digest(
    actor_id: str,
    operation: str,
    resource_id: str,
    parameters: dict[str, Any],
) -> str:
    for field_name, value in (
        ("actor_id", actor_id),
        ("operation", operation),
        ("resource_id", resource_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a JSON object")
    action = {
        "actor_id": actor_id,
        "operation": operation,
        "resource_id": resource_id,
        "parameters": parameters,
    }
    return hashlib.sha256(_canonical_json(action).encode("utf-8")).hexdigest()


class AuthorizationHarness:
    """SQLite-backed demo of exact-scope, expiring, single-use approvals.

    Each execute attempt starts with BEGIN IMMEDIATE. This serializes competing
    consumers in this single SQLite database so only one can change an
    APPROVED record to CONSUMED. It is not a distributed lock or HA design.
    """

    def __init__(self, db_path: str | Path, clock: Callable[[], datetime] = _utc_now):
        self.db_path = str(db_path)
        self.clock = clock
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=15, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 15000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    actor_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    action_digest TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    issued_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('APPROVED', 'CONSUMED', 'EXPIRED')),
                    consumed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE TRIGGER IF NOT EXISTS audit_events_no_update
                BEFORE UPDATE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'audit_events is append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
                BEFORE DELETE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'audit_events is append-only');
                END;
                """
            )
        finally:
            connection.close()

    def _append_event(self, connection: sqlite3.Connection, event: dict[str, Any]) -> None:
        previous = connection.execute(
            "SELECT event_hash FROM audit_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else GENESIS_HASH
        encoded = _canonical_json(event)
        event_hash = hashlib.sha256(
            (previous_hash + "\n" + encoded).encode("utf-8")
        ).hexdigest()
        connection.execute(
            "INSERT INTO audit_events(event_json, previous_hash, event_hash) VALUES (?, ?, ?)",
            (encoded, previous_hash, event_hash),
        )

    def issue_approval(
        self,
        *,
        actor_id: str,
        operation: str,
        resource_id: str,
        parameters: dict[str, Any],
        approved_by: str,
        ttl_seconds: int = 300,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> dict[str, str]:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if not isinstance(approved_by, str) or not approved_by.strip():
            raise ValueError("approved_by must be a non-empty string")
        if not isinstance(policy_version, str) or not policy_version.strip():
            raise ValueError("policy_version must be a non-empty string")

        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        now = now.astimezone(timezone.utc)
        issued_at = _iso(now)
        expires_at = _iso(now + timedelta(seconds=ttl_seconds))
        approval_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        digest = _action_digest(actor_id, operation, resource_id, parameters)

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO approvals (
                    approval_id, token_hash, actor_id, operation, resource_id,
                    action_digest, policy_version, approved_by, issued_at,
                    expires_at, status, consumed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', NULL)""",
                (
                    approval_id,
                    token_hash,
                    actor_id,
                    operation,
                    resource_id,
                    digest,
                    policy_version,
                    approved_by,
                    issued_at,
                    expires_at,
                ),
            )
            self._append_event(
                connection,
                {
                    "event": "APPROVAL_ISSUED",
                    "timestamp": issued_at,
                    "approval_id": approval_id,
                    "actor_id": actor_id,
                    "operation": operation,
                    "resource_id": resource_id,
                    "action_digest": digest,
                    "policy_version": policy_version,
                    "approved_by": approved_by,
                    "expires_at": expires_at,
                },
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        # The raw bearer token is returned once and is never stored in SQLite.
        return {
            "approval_id": approval_id,
            "token": token,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "action_digest": digest,
            "policy_version": policy_version,
        }

    def record_denial(
        self,
        *,
        actor_id: str,
        operation: str,
        resource_id: str,
        parameters: dict[str, Any],
        denied_by: str,
        reason: str,
    ) -> dict[str, str]:
        """Record an explicit approval denial without issuing an executable token."""
        if not isinstance(denied_by, str) or not denied_by.strip():
            raise ValueError("denied_by must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")
        digest = _action_digest(actor_id, operation, resource_id, parameters)
        timestamp = _iso(self._now_utc())
        event_id = str(uuid.uuid4())
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._append_event(
                connection,
                {
                    "event": "APPROVAL_DENIED",
                    "timestamp": timestamp,
                    "event_id": event_id,
                    "actor_id": actor_id,
                    "operation": operation,
                    "resource_id": resource_id,
                    "action_digest": digest,
                    "denied_by": denied_by,
                    "reason": reason,
                },
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {"verdict": "DENIED", "reason": reason, "event_id": event_id}

    def execute(
        self,
        *,
        token: str,
        actor_id: str,
        operation: str,
        resource_id: str,
        parameters: dict[str, Any],
        executor: Callable[[dict[str, Any]], Any],
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        attempted_now = self.clock()
        if attempted_now.tzinfo is None or attempted_now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        attempted_at = _iso(attempted_now.astimezone(timezone.utc))
        digest = _action_digest(actor_id, operation, resource_id, parameters)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest() if token else ""
        action = {
            "actor_id": actor_id,
            "operation": operation,
            "resource_id": resource_id,
            "parameters": parameters,
        }
        denial: str | None = None
        approval_id: str | None = None
        policy_version: str | None = None

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            approval = connection.execute(
                "SELECT * FROM approvals WHERE token_hash = ?", (token_hash,)
            ).fetchone()

            if approval is None:
                denial = "APPROVAL_NOT_FOUND"
            else:
                approval_id = approval["approval_id"]
                policy_version = approval["policy_version"]
                if actor_id != approval["actor_id"]:
                    denial = "ACTOR_MISMATCH"
                elif digest != approval["action_digest"]:
                    denial = "SCOPE_MISMATCH"
                elif approval["status"] != "APPROVED":
                    denial = "APPROVAL_ALREADY_CONSUMED" if approval["status"] == "CONSUMED" else "APPROVAL_NOT_ACTIVE"
                elif self._now_utc() >= _parse_iso(approval["expires_at"]):
                    connection.execute(
                        "UPDATE approvals SET status = 'EXPIRED' WHERE approval_id = ? AND status = 'APPROVED'",
                        (approval_id,),
                    )
                    denial = "APPROVAL_EXPIRED"

            if denial:
                self._append_event(
                    connection,
                    {
                        "event": "EXECUTION_DENIED",
                        "timestamp": attempted_at,
                        "request_id": request_id,
                        "approval_id": approval_id,
                        "actor_id": actor_id,
                        "operation": operation,
                        "resource_id": resource_id,
                        "action_digest": digest,
                        "policy_version": policy_version,
                        "reason": denial,
                    },
                )
                connection.commit()
                return {"request_id": request_id, "verdict": "DENIED", "reason": denial}

            consumed_at = _iso(self._now_utc())
            changed = connection.execute(
                """UPDATE approvals SET status = 'CONSUMED', consumed_at = ?
                   WHERE approval_id = ? AND status = 'APPROVED' AND consumed_at IS NULL""",
                (consumed_at, approval_id),
            ).rowcount
            if changed != 1:
                denial = "APPROVAL_ALREADY_CONSUMED"
                self._append_event(
                    connection,
                    {
                        "event": "EXECUTION_DENIED",
                        "timestamp": consumed_at,
                        "request_id": request_id,
                        "approval_id": approval_id,
                        "actor_id": actor_id,
                        "operation": operation,
                        "resource_id": resource_id,
                        "action_digest": digest,
                        "policy_version": policy_version,
                        "reason": denial,
                    },
                )
                connection.commit()
                return {"request_id": request_id, "verdict": "DENIED", "reason": denial}

            self._append_event(
                connection,
                {
                    "event": "APPROVAL_CONSUMED",
                    "timestamp": consumed_at,
                    "request_id": request_id,
                    "approval_id": approval_id,
                    "actor_id": actor_id,
                    "operation": operation,
                    "resource_id": resource_id,
                    "action_digest": digest,
                    "policy_version": policy_version,
                },
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        # The side effect occurs only after the one-time approval is committed.
        # In production, pass request_id as a downstream idempotency key and
        # reconcile ambiguous outcomes; SQLite cannot atomically commit a remote action.
        try:
            execution_result = executor(action)
        except Exception as exc:  # Deliberately record type only, not arbitrary secret-bearing text.
            self._record_followup_event(
                {
                    "event": "EXECUTION_FAILED",
                    "timestamp": _iso(self._now_utc()),
                    "request_id": request_id,
                    "approval_id": approval_id,
                    "failure_type": type(exc).__name__,
                }
            )
            return {
                "request_id": request_id,
                "approval_id": approval_id,
                "verdict": "AUTHORIZED_EXECUTION_FAILED",
                "reason": "EXECUTOR_EXCEPTION",
            }

        self._record_followup_event(
            {
                "event": "EXECUTION_SUCCEEDED",
                "timestamp": _iso(self._now_utc()),
                "request_id": request_id,
                "approval_id": approval_id,
                "result_digest": hashlib.sha256(_canonical_json(execution_result).encode("utf-8")).hexdigest(),
            }
        )
        return {
            "request_id": request_id,
            "approval_id": approval_id,
            "verdict": "AUTHORIZED_SANDBOX_EXECUTED",
            "execution_result": execution_result,
        }

    def _now_utc(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)

    def _record_followup_event(self, event: dict[str, Any]) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._append_event(connection, event)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def verify_audit_chain(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT event_id, event_json, previous_hash, event_hash FROM audit_events ORDER BY event_id"
            ).fetchall()
        finally:
            connection.close()
        expected_previous = GENESIS_HASH
        for row in rows:
            if row["previous_hash"] != expected_previous:
                return {"valid": False, "checked_events": row["event_id"] - 1, "failed_event_id": row["event_id"]}
            computed = hashlib.sha256(
                (expected_previous + "\n" + row["event_json"]).encode("utf-8")
            ).hexdigest()
            if computed != row["event_hash"]:
                return {"valid": False, "checked_events": row["event_id"] - 1, "failed_event_id": row["event_id"]}
            expected_previous = row["event_hash"]
        return {
            "valid": True,
            "checked_events": len(rows),
            "tip_hash": expected_previous,
        }

    def get_audit_events(self) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT event_id, event_json, previous_hash, event_hash FROM audit_events ORDER BY event_id"
            ).fetchall()
        finally:
            connection.close()
        return [
            {
                "event_id": row["event_id"],
                **json.loads(row["event_json"]),
                "previous_hash": row["previous_hash"],
                "event_hash": row["event_hash"],
            }
            for row in rows
        ]


def classify_independent_observation(
    claimed_success: bool,
    independent_observation: dict[str, Any] | None,
) -> str:
    """Do not treat an execution claim as proof when no independent receipt exists."""
    if independent_observation is None:
        return "UNKNOWN"
    observed = independent_observation.get("effect_observed") is True
    if claimed_success:
        return "PASS" if observed else "FAIL"
    return "FAIL" if observed else "PASS"
