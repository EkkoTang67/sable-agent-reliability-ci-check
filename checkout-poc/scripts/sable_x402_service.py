"""Small importable wrapper that builds a report from read-only public sources."""
from __future__ import annotations
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable
from sable_x402_closure import assess
from sable_x402_collect import BASE, SETTLEMENTS_URL, SNAPSHOT_URL, fetch_json, normalize_live_case


def collect_report(case: dict[str, str], fetcher: Callable[[str], Any] | None = None) -> dict[str, Any]:
    get_json = fetcher or (lambda url: fetch_json(url, timeout=3.5))
    urls = {
        "recent_settlements": SETTLEMENTS_URL,
        "capability_snapshot": f"{SNAPSHOT_URL}?slug={case['slug']}&n=10",
        "chain_transaction": f"{BASE}/transactions/{case['transaction_hash']}",
        "token_transfers": f"{BASE}/transactions/{case['transaction_hash']}/token-transfers?type=ERC-20",
    }
    sources: dict[str, Any] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = {pool.submit(get_json, url): name for name, url in urls.items()}
        for future in as_completed(tasks):
            name = tasks[future]
            try:
                sources[name] = future.result()
            except Exception as exc:
                errors[name] = f"{type(exc).__name__}: {str(exc)[:400]}"
    dossier = normalize_live_case(
        tx_hash=case["transaction_hash"], slug=case["slug"], expected_amount=case["expected_amount"],
        recipient=case["recipient"], asset=case["asset"], asset_contract=case["asset_contract"],
        endpoint=case["endpoint"], network=case["network"], sources=sources, source_errors=errors,
        response_receipt=None,
    )
    report = assess(dossier)
    report["mode"] = "live_public_sources_read_only" if sources else "public_source_fetch_failed"
    report["collector"] = {"read_only": True, "paid_endpoint_called": False, "submitted_payment": False, "fetched_sources": list(sources.keys()), "source_errors": errors, "automatic_fulfillment": True}
    report.pop("report_sha256", None)
    report["delivery_policy"] = {"if_no_public_sources": "refund_required", "verdict_does_not_promise_positive_outcome": True, "historical_paid_response_not_proven_without_receipt": True}
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["report_sha256"] = hashlib.sha256(canonical).hexdigest()
    return report
