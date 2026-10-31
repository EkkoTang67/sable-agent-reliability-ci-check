"""Local-only reference harness for eight agent authorization failure cases.
No network calls, production writes, credentials, or real side effects.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
import json
import unittest


@dataclass(frozen=True)
class Action:
    actor: str
    tenant: str
    operation: str
    target: str
    parameters: dict

    @property
    def digest(self):
        raw = json.dumps(self.parameters, sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode()).hexdigest()


@dataclass
class Approval:
    actor: str
    tenant: str
    operation: str
    target: str
    digest: str
    expires_at: int
    approved: bool = True
    consumed: bool = False


class Harness:
    def __init__(self):
        self.lock = Lock()
        self.approvals = {}
        self.effects = []
        self.events = []

    def approve(self, token, action, expires_at, approved=True):
        with self.lock:
            self.approvals[token] = Approval(
                action.actor, action.tenant, action.operation, action.target,
                action.digest, expires_at, approved
            )

    def execute(self, action, token, now, route="primary",
                guard_available=True, approver_available=True):
        # Atomic only inside this process; not a distributed lock.
        with self.lock:
            reason = None
            approval = self.approvals.get(token) if token else None
            if not guard_available:
                reason = "authorization_guard_unavailable"
            elif not approver_available:
                reason = "approver_unavailable"
            elif approval is None:
                reason = "approval_missing"
            elif not approval.approved:
                reason = "explicitly_denied"
            elif now >= approval.expires_at:
                reason = "approval_expired"
            elif (approval.actor, approval.tenant, approval.operation,
                  approval.target, approval.digest) != (
                  action.actor, action.tenant, action.operation,
                  action.target, action.digest):
                reason = "approval_scope_mismatch"
            elif approval.consumed:
                reason = "approval_already_consumed"

            event = {
                "event_id": f"evt-{len(self.events)+1:04d}",
                "actor": action.actor,
                "requested_operation": action.operation,
                "authorization_decision": "DENY" if reason else "ALLOW",
                "execution_result": "NOT_EXECUTED" if reason else "EXECUTED",
                "denial_reason": reason,
                "route": route,
            }
            self.events.append(event)
            if reason:
                return {"allowed": False, "reason": reason, "event": event}

            approval.consumed = True
            effect = {
                "effect_id": f"effect-{len(self.effects)+1:04d}",
                "actor": action.actor, "tenant": action.tenant,
                "operation": action.operation, "target": action.target,
                "parameter_digest": action.digest, "route": route,
            }
            self.effects.append(effect)
            return {"allowed": True, "effect": effect, "event": event}

    @staticmethod
    def independent_verdict(claimed_success, observed_effects):
        if observed_effects is None:
            return "UNKNOWN"
        if claimed_success:
            return "PASS" if len(observed_effects) == 1 else "FAIL"
        return "FAIL" if observed_effects else "PASS"


def run_cases():
    out = []

    def record(case_id, name, expected, observed, evidence, ok):
        out.append({"case_id": case_id, "scenario": name,
                    "verdict": "PASS" if ok else "FAIL",
                    "expected": expected, "observed": observed,
                    "evidence": evidence})

    # AB-01 explicit denial
    h = Harness(); a = Action("u1", "t1", "send", "mailbox", {"to": "x"})
    h.approve("d", a, 99, approved=False); r = h.execute(a, "d", 1)
    record("AB-01", "explicit denial", "no side effect", r, h.events, not r["allowed"] and not h.effects)

    # AB-02 no approver / unattended run
    h = Harness(); a = Action("u1", "t1", "pay", "invoice", {"amount": 10})
    h.approve("a", a, 99); r = h.execute(a, "a", 1, approver_available=False)
    record("AB-02", "approver unavailable", "fail closed", r, h.events, not r["allowed"] and not h.effects)

    # AB-03 alternate tool cannot bypass boundary
    h = Harness(); a = Action("u1", "t1", "delete", "record", {"id": 1})
    r = h.execute(a, None, 1, route="alternate-tool")
    record("AB-03", "alternate-tool route", "same protected effect denied", r, h.events, not r["allowed"] and not h.effects)

    # AB-04 authorization guard exception
    h = Harness(); a = Action("u1", "t1", "update", "record", {"v": 2})
    h.approve("a", a, 99); r = h.execute(a, "a", 1, guard_available=False)
    record("AB-04", "guard exception", "fail closed", r, h.events, not r["allowed"] and not h.effects)

    # AB-05 mixed tool batch ordering
    results = []
    for order in (("protected", "read"), ("read", "protected")):
        h = Harness(); a = Action("u1", "t1", "write", "record", {"v": 2})
        h.approve("d", a, 99, approved=False)
        for item in order:
            if item == "protected":
                results.append(h.execute(a, "d", 1)["allowed"])
    record("AB-05", "mixed tool batch/order", "denied in both orders",
           results, {"orderings": 2}, results == [False, False])

    # AB-06 expired and wrong-scope (including parameter tampering)
    h = Harness(); a = Action("u1", "t1", "update", "acct", {"bank": "A"})
    h.approve("expired", a, 5); expired = h.execute(a, "expired", 5)
    h.approve("scope", a, 99)
    changed = Action("u1", "t1", "update", "acct", {"bank": "B"})
    mismatch = h.execute(changed, "scope", 1)
    ok = not expired["allowed"] and not mismatch["allowed"] and not h.effects
    record("AB-06", "stale/wrong-scope approval", "both denied",
           [expired, mismatch], h.events, ok)

    # AB-07 concurrent reuse of a one-time approval
    h = Harness(); a = Action("u1", "t1", "release", "batch", {"id": 7})
    h.approve("once", a, 99)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: h.execute(a, "once", 1), range(8)))
    successes = sum(x["allowed"] for x in results)
    record("AB-07", "concurrent one-time approval/replay",
           "exactly one success and one effect", successes,
           {"events": h.events, "effects": h.effects},
           successes == 1 and len(h.effects) == 1)

    # AB-08 claimed success without independent observation
    verdict = Harness.independent_verdict(True, None)
    record("AB-08", "claim vs independent effect",
           "UNKNOWN when authoritative observation absent", verdict,
           {"claimed_success": True, "observation": None}, verdict == "UNKNOWN")
    return out


def build_report():
    cases = run_cases()
    return {
        "report_type": "synthetic_agent_authorization_test",
        "status": "SYNTHETIC_REFERENCE_HARNESS_ONLY",
        "execution_boundary": "local in-memory simulator; no external side effects",
        "summary": {
            "total": len(cases),
            "pass": sum(x["verdict"] == "PASS" for x in cases),
            "fail": sum(x["verdict"] == "FAIL" for x in cases),
        },
        "cases": cases,
        "limitations": [
            "Not a production authorization gateway.",
            "The lock is process-local, not a distributed transaction lock.",
            "Does not test a real agent framework, identity provider, database, or tool runtime.",
            "A buyer engagement requires an authorized sandbox and target-specific acceptance criteria."
        ],
    }


class HarnessTests(unittest.TestCase):
    def test_all_eight_reference_scenarios(self):
        report = build_report()
        self.assertEqual(report["summary"], {"total": 8, "pass": 8, "fail": 0})

    def test_eight_concurrent_replays_only_one_effect(self):
        h = Harness(); a = Action("u", "t", "release", "b", {"x": 1})
        h.approve("one", a, 100)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: h.execute(a, "one", 1), range(8)))
        self.assertEqual(sum(x["allowed"] for x in results), 1)
        self.assertEqual(len(h.effects), 1)

    def test_cross_tenant_and_parameter_tampering_denied(self):
        h = Harness(); approved = Action("u", "tenant-a", "pay", "inv", {"amount": 10})
        h.approve("a", approved, 100)
        changed = Action("u", "tenant-b", "pay", "inv", {"amount": 1000})
        result = h.execute(changed, "a", 1)
        self.assertFalse(result["allowed"])
        self.assertEqual(h.effects, [])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.test:
        unittest.main(argv=["agent_authorization_harness"], verbosity=2)
    else:
        report = build_report()
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(rendered + "\n")
        print(rendered)
