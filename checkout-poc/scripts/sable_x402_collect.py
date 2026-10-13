#!/usr/bin/env python3
"""Read-only public evidence collector for an x402 transaction.

Queries public settlement/service metadata and the Base Blockscout explorer only.
Never calls the paid resource endpoint, creates a wallet/payment, or submits a transaction.
The collector is conservative: a record absent from a limited public feed is UNKNOWN, not a failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from sable_x402_closure import assess

TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
BASE = "https://base.blockscout.com/api/v2"
SETTLEMENTS_URL = "https://x402-agent-pay.com/facilitator/recent-settlements"
SNAPSHOT_URL = "https://agentpaystore.com/api/agent/capability-snapshot"
BASE_NATIVE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


def fetch_json(url: str, timeout: float = 12.0) -> Any:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "SABLE-x402-readonly-auditor/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(5_000_000)
        if len(body) >= 5_000_000:
            raise ValueError("response exceeded 5 MB safety limit")
        return json.loads(body.decode("utf-8"))


def iter_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from iter_dicts(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_dicts(nested)


def find_tx_record(value: Any, tx_hash: str) -> dict[str, Any] | None:
    tx = tx_hash.lower()
    for item in iter_dicts(value):
        if any(str(item.get(key, "")).lower() == tx for key in ("tx", "tx_hash", "transaction_hash", "transaction")):
            return item
    return None


def items_of(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        return [x for x in value["items"] if isinstance(x, dict)]
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    return []


def get_hash(obj: Any) -> str | None:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for key in ("hash", "transaction_hash", "tx_hash", "tx"):
            if isinstance(obj.get(key), str):
                return obj[key]
    return None


def normalized_amount(transfer: dict[str, Any]) -> str | None:
    token = transfer.get("token") or {}
    total = transfer.get("total") or {}
    raw_value = total.get("value", transfer.get("total_value", transfer.get("value")))
    decimals = token.get("decimals", transfer.get("token_decimals"))
    try:
        if raw_value is None or decimals is None:
            return None
        amount = Decimal(str(raw_value)) / (Decimal(10) ** int(decimals))
        return format(amount.normalize(), "f")
    except (InvalidOperation, ValueError, TypeError):
        return None


def token_contract_of(transfer: dict[str, Any]) -> str | None:
    token = transfer.get("token") or {}
    value = token.get("address_hash", token.get("address", token.get("hash")))
    return value if isinstance(value, str) else None


def recipient_of(transfer: dict[str, Any]) -> str | None:
    value = transfer.get("to")
    if isinstance(value, dict):
        value = value.get("hash")
    return value if isinstance(value, str) else None


def normalize_live_case(*, tx_hash: str, slug: str, expected_amount: str, recipient: str,
                        asset: str, asset_contract: str, endpoint: str, network: str,
                        sources: dict[str, Any], source_errors: dict[str, str],
                        response_receipt: dict[str, Any] | None = None) -> dict[str, Any]:
    settlement_data = sources.get("recent_settlements")
    service_data = sources.get("capability_snapshot")
    chain_data = sources.get("chain_transaction")
    transfer_data = sources.get("token_transfers")
    settlement_record = find_tx_record(settlement_data, tx_hash) if settlement_data is not None else None
    service_record = find_tx_record(service_data, tx_hash) if service_data is not None else None
    settlement = None
    if chain_data is not None and transfer_data is not None:
        chain_hash = get_hash(chain_data)
        status = chain_data.get("status") if isinstance(chain_data, dict) else None
        if status is None and isinstance(chain_data, dict):
            status = chain_data.get("result")
        all_transfers = items_of(transfer_data)
        expected_recipient_transfers = [item for item in all_transfers if (recipient_of(item) or "").lower() == recipient.lower()]
        expected_contract_transfers = [item for item in all_transfers if (token_contract_of(item) or "").lower() == asset_contract.lower()]
        expected_amount_normalized = format(Decimal(expected_amount).normalize(), "f")
        recipient_exact = [item for item in expected_recipient_transfers if str(((item.get("token") or {}).get("symbol", ""))).lower() == asset.lower()]
        exact = [item for item in recipient_exact if (token_contract_of(item) or "").lower() == asset_contract.lower() and normalized_amount(item) == expected_amount_normalized]
        if len(exact) == 1:
            transfer = exact[0]
        elif len(expected_recipient_transfers) == 1:
            transfer = expected_recipient_transfers[0]
        elif len(expected_contract_transfers) == 1:
            transfer = expected_contract_transfers[0]
        elif len(all_transfers) == 1:
            transfer = all_transfers[0]
        else:
            transfer = None
        if chain_hash and chain_hash.lower() == tx_hash.lower() and transfer is not None:
            token = transfer.get("token") or {}
            amount = normalized_amount(transfer)
            status_text = str(status or "").lower()
            settled_status = "success" if status_text in {"ok", "success", "confirmed"} else ("reverted" if status_text in {"error", "reverted", "failed"} else str(status or "unknown"))
            settlement = {"transaction_hash": chain_hash, "status": settled_status, "network": network, "recipient": recipient_of(transfer), "amount": amount, "asset": token.get("symbol"), "asset_contract": token_contract_of(transfer), "source_url": f"{BASE}/transactions/{tx_hash}", "independent_source": True}
    service = None
    if service_data is not None:
        latest = service_data.get("latest") if isinstance(service_data, dict) else None
        if isinstance(latest, dict) and get_hash(latest) and get_hash(latest).lower() == tx_hash.lower():
            service = latest
        elif service_record is not None:
            service = service_record
    if service is not None:
        service_tx = get_hash(service)
        service = {"transaction_hash": service_tx, "endpoint": service.get("endpoint"), "price_usd": service.get("price_usd"), "valid": service_data.get("valid") if isinstance(service_data, dict) else service.get("valid"), "match_score": service_data.get("match_score") if isinstance(service_data, dict) else service.get("match_score"), "source_url": f"{SNAPSHOT_URL}?slug={urllib.parse.quote(slug)}&n=10", "independent_source": False}
    delivery: dict[str, Any] = {"response_receipt": response_receipt, "downstream_readback": None}
    if not response_receipt:
        delivery["source_observation"] = "No paid endpoint was called and no response receipt was supplied to this collector."
    evidence_case = {
        "case_id": f"x402-{slug}-{tx_hash[:12]}",
        "claim": "The expected paid service response is bound to the same payment and satisfies the declared outcome.",
        "expected": {"transaction_hash": tx_hash, "network": network, "recipient": recipient, "amount": str(expected_amount), "asset": asset, "asset_contract": asset_contract, "endpoint": endpoint},
        "observations": {"settlement": settlement, "service_record": service, "delivery": delivery},
        "source_dossier_claims": [],
    }
    if settlement_record is not None:
        evidence_case["source_dossier_claims"].append({"source": SETTLEMENTS_URL, "claim": "The provider's public settlement feed contains the requested transaction.", "evidence_scope": "provider-published settlement metadata", "record": settlement_record})
    else:
        evidence_case["source_dossier_claims"].append({"source": SETTLEMENTS_URL, "claim": "No matching transaction was found in the fetched public feed snapshot; feed coverage may be limited.", "evidence_scope": "provider-published settlement metadata; absence is not a failure verdict"})
    for name, raw in sources.items():
        canonical = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evidence_case["source_dossier_claims"].append({"source_name": name, "source_status": "fetched", "source_type": "public_read_only", "source_sha256": hashlib.sha256(canonical).hexdigest(), "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")})
    for name, error in source_errors.items():
        evidence_case["source_dossier_claims"].append({"source_name": name, "source_status": "unavailable", "error": error})
    return evidence_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tx", required=True, help="0x-prefixed 32-byte transaction hash")
    parser.add_argument("--slug", default="feeds", help="Public AgentPay capability slug (default: feeds)")
    parser.add_argument("--amount", required=True, help="Expected token amount, e.g. 0.05")
    parser.add_argument("--recipient", required=True, help="Expected treasury/recipient address")
    parser.add_argument("--asset", default="USDC", help="Expected token symbol (USDC only for this prototype)")
    parser.add_argument("--asset-contract", default=BASE_NATIVE_USDC, help="Expected native USDC contract on Base")
    parser.add_argument("--endpoint", required=True, help="Expected paid endpoint")
    parser.add_argument("--network", default="eip155:8453", help="CAIP-2 network identifier (Base mainnet default)")
    parser.add_argument("--receipt-json", help="Optional local authoritative response-receipt JSON; does not call the paid service")
    parser.add_argument("--output", default="sable-x402-live-audit.json", help="Output JSON path")
    args = parser.parse_args(argv)
    if not TX_RE.fullmatch(args.tx):
        parser.error("--tx must be a 0x-prefixed 32-byte hash")
    urls = {
        "recent_settlements": SETTLEMENTS_URL,
        "capability_snapshot": f"{SNAPSHOT_URL}?slug={urllib.parse.quote(args.slug)}&n=10",
        "chain_transaction": f"{BASE}/transactions/{args.tx}",
        "token_transfers": f"{BASE}/transactions/{args.tx}/token-transfers?type=ERC-20",
    }
    sources: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for name, url in urls.items():
        try:
            sources[name] = fetch_json(url)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
    receipt = None
    if args.receipt_json:
        try:
            receipt = json.loads(Path(args.receipt_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"could not read --receipt-json: {exc}")
    case = normalize_live_case(tx_hash=args.tx, slug=args.slug, expected_amount=args.amount, recipient=args.recipient, asset=args.asset, asset_contract=args.asset_contract, endpoint=args.endpoint, network=args.network, sources=sources, source_errors=errors, response_receipt=receipt)
    report = assess(case)
    report["mode"] = "live_public_sources_read_only" if sources else "public_source_fetch_failed"
    report["collector"] = {"read_only": True, "paid_endpoint_called": False, "submitted_payment": False, "source_errors": errors, "fetched_sources": list(sources.keys())}
    report.pop("report_sha256", None)
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["report_sha256"] = hashlib.sha256(canonical).hexdigest()
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_verdict": report["overall_verdict"], "component_verdicts": {k: v["verdict"] for k, v in report["components"].items()}, "fetched_sources": list(sources.keys()), "source_errors": errors, "output": args.output, "report_sha256": report["report_sha256"]}, ensure_ascii=False, indent=2))
    return 0 if report["overall_verdict"] == "VERIFIED" else 1 if report["overall_verdict"] == "NOT_VERIFIED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
