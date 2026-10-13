"""Strict evidence-bundle verifier for x402-receipts/v0 (Base USDC only).

The caller supplies a signed receipt, exact response-body bytes (base64), trusted
seller signer address, expected transaction hash, exact request URL/method and exact
serialized params. The module independently checks the receipt signature, request/body
hashes, and Base settlement fields. Unsupported chains stay UNKNOWN.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler
from typing import Any, Callable
from urllib.parse import urlsplit

from eth_account import Account
from eth_account.messages import encode_typed_data

from api.common import json_response, method_not_allowed, origin_is_allowed
from scripts.sable_x402_collect import (
    BASE_CHAIN_ID,
    BASE_NATIVE_USDC,
    BASE_RPC_URLS,
    fetch_base_rpc_evidence,
    fetch_json_rpc,
)

MAX_REQUEST_BYTES = 262_144
MAX_RESPONSE_BODY_BYTES = 131_072
TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
HEX32_RE = re.compile(r"^(?:0x)?[0-9a-fA-F]{64}$")
ZERO_BYTES32 = "0x" + "0" * 64

SELLER_TYPES = {
    "Receipt": [
        {"name": "scheme", "type": "string"},
        {"name": "sellerAgentId", "type": "string"},
        {"name": "payment", "type": "Payment"},
        {"name": "request", "type": "Request"},
        {"name": "response", "type": "Response"},
    ],
    "Payment": [
        {"name": "chainId", "type": "uint256"},
        {"name": "txHash", "type": "bytes32"},
        {"name": "asset", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "payer", "type": "address"},
        {"name": "payee", "type": "address"},
    ],
    "Request": [
        {"name": "method", "type": "string"},
        {"name": "urlHash", "type": "bytes32"},
        {"name": "paramsHash", "type": "bytes32"},
        {"name": "ts", "type": "string"},
    ],
    "Response": [
        {"name": "status", "type": "uint256"},
        {"name": "bodySha256", "type": "bytes32"},
        {"name": "contentType", "type": "string"},
        {"name": "ts", "type": "string"},
        {"name": "latencyMs", "type": "uint256"},
    ],
}
PAYMENT_V03_FIELDS = [
    {"name": "chainId", "type": "uint256"},
    {"name": "txHash", "type": "bytes32"},
    {"name": "asset", "type": "string"},
    {"name": "amount", "type": "string"},
    {"name": "payer", "type": "address"},
    {"name": "payee", "type": "address"},
    {"name": "assetAddress", "type": "string"},
]
V03_TYPES = {
    "ReceiptV03": [
        {"name": "scheme", "type": "string"},
        {"name": "sellerAgentId", "type": "string"},
        {"name": "payment", "type": "PaymentV03"},
        {"name": "paymentRequirementsHash", "type": "bytes32"},
        {"name": "request", "type": "Request"},
        {"name": "response", "type": "Response"},
    ],
    "PaymentV03": PAYMENT_V03_FIELDS,
    "Request": SELLER_TYPES["Request"],
    "Response": SELLER_TYPES["Response"],
}


def _verdict(value: str, reason: str, **details: Any) -> dict[str, Any]:
    return {"verdict": value, "reason": reason, **details}


def _field(obj: Any, key: str) -> Any:
    return obj.get(key) if isinstance(obj, dict) else None


def _bytes32(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX32_RE.fullmatch(value):
        raise ValueError(f"{field} must be a 32-byte hex digest")
    return value if value.startswith("0x") else "0x" + value


def _typed_receipt(receipt: dict[str, Any], version03: bool) -> tuple[dict[str, Any], dict[str, Any], str]:
    payment = receipt["payment"]
    request = receipt["request"]
    response = receipt["response"]
    seller = receipt["seller"]
    if version03:
        message = {
            "scheme": receipt["scheme"],
            "sellerAgentId": seller["erc8004_agent_id"],
            "payment": {
                "chainId": int(payment["chain_id"]),
                "txHash": _bytes32(payment["tx_hash"], "payment.tx_hash"),
                "asset": str(payment["asset"]),
                "amount": str(payment["amount"]),
                "payer": payment["payer"],
                "payee": payment["payee"],
                "assetAddress": str(payment.get("asset_address") or ""),
            },
            "paymentRequirementsHash": _bytes32(
                request.get("payment_requirements_sha256") or ZERO_BYTES32,
                "request.payment_requirements_sha256",
            ),
            "request": {
                "method": str(request["method"]),
                "urlHash": _bytes32(request["url_hash"], "request.url_hash"),
                "paramsHash": _bytes32(request["params_hash"], "request.params_hash"),
                "ts": str(request["ts"]),
            },
            "response": {
                "status": int(response["status"]),
                "bodySha256": _bytes32(response["body_sha256"], "response.body_sha256"),
                "contentType": str(response["content_type"]),
                "ts": str(response["ts"]),
                "latencyMs": int(response["latency_ms"]),
            },
        }
        domain = {"name": "x402-receipts", "version": "0.3", "chainId": int(payment["chain_id"])}
        return domain, message, "ReceiptV03"
    message = {
        "scheme": receipt["scheme"],
        "sellerAgentId": seller["erc8004_agent_id"],
        "payment": {
            "chainId": int(payment["chain_id"]),
            "txHash": _bytes32(payment["tx_hash"], "payment.tx_hash"),
            "asset": str(payment["asset"]),
            "amount": str(payment["amount"]),
            "payer": payment["payer"],
            "payee": payment["payee"],
        },
        "request": {
            "method": str(request["method"]),
            "urlHash": _bytes32(request["url_hash"], "request.url_hash"),
            "paramsHash": _bytes32(request["params_hash"], "request.params_hash"),
            "ts": str(request["ts"]),
        },
        "response": {
            "status": int(response["status"]),
            "bodySha256": _bytes32(response["body_sha256"], "response.body_sha256"),
            "contentType": str(response["content_type"]),
            "ts": str(response["ts"]),
            "latencyMs": int(response["latency_ms"]),
        },
    }
    domain = {"name": "x402-receipts", "version": "0", "chainId": int(payment["chain_id"])}
    return domain, message, "Receipt"


def _verify_seller_signature(receipt: Any, expected_signer: str) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        return _verdict("NOT_VERIFIED", "receipt must be a JSON object")
    for name in ("payment", "request", "response", "seller"):
        if not isinstance(receipt.get(name), dict):
            return _verdict("NOT_VERIFIED", f"receipt.{name} must be an object")
    if receipt.get("scheme") != "x402-receipts/v0":
        return _verdict("NOT_VERIFIED", "receipt.scheme is not x402-receipts/v0")
    if not ADDR_RE.fullmatch(expected_signer or ""):
        return _verdict("NOT_VERIFIED", "expected_seller_address must be a 20-byte EVM address")
    signature = receipt["seller"].get("sig")
    if not isinstance(signature, str) or not signature.startswith("0x"):
        return _verdict("NOT_VERIFIED", "receipt.seller.sig is missing or not a 0x-prefixed signature")

    errors: list[str] = []
    recovered: list[dict[str, str]] = []
    for version03, types in ((True, V03_TYPES), (False, SELLER_TYPES)):
        try:
            domain, message, primary_type = _typed_receipt(receipt, version03)
            signable = encode_typed_data(domain_data=domain, message_types=types, message_data=message)
            signer = Account.recover_message(signable, signature=signature)
            recovered.append({"domain_version": domain["version"], "address": signer})
            if signer.lower() == expected_signer.lower():
                payee = receipt["payment"]["payee"]
                return _verdict(
                    "VERIFIED",
                    "EIP-712 seller signature recovered to the externally supplied expected signer.",
                    recovered_signer=signer,
                    expected_signer=expected_signer,
                    signature_domain_version=domain["version"],
                    signer_matches_payment_payee=(signer.lower() == str(payee).lower()),
                )
        except Exception as exc:
            errors.append(f"{'0.3' if version03 else '0'}:{type(exc).__name__}")
    return _verdict(
        "NOT_VERIFIED",
        "Seller signature did not recover to the expected seller address under supported x402-receipts domains.",
        expected_signer=expected_signer,
        recovered_signers=recovered,
        parse_errors=errors,
    )


def _verify_request_binding(receipt: dict[str, Any], expected_url: str, expected_method: str, expected_params_json: str) -> dict[str, Any]:
    request = receipt.get("request") or {}
    actual_url_hash = hashlib.sha256(expected_url.encode("utf-8")).hexdigest()
    actual_params_hash = hashlib.sha256(expected_params_json.encode("utf-8")).hexdigest()
    claimed_url_hash = str(request.get("url_hash", "")).lower().removeprefix("0x")
    claimed_params_hash = str(request.get("params_hash", "")).lower().removeprefix("0x")
    claimed_method = str(request.get("method", ""))
    mismatches = []
    if claimed_method.upper() != expected_method.upper():
        mismatches.append("method_mismatch")
    if claimed_url_hash != actual_url_hash:
        mismatches.append("url_hash_mismatch")
    if claimed_params_hash != actual_params_hash:
        mismatches.append("params_hash_mismatch")
    if mismatches:
        return _verdict(
            "NOT_VERIFIED",
            "The signed receipt's request fields do not match the caller-supplied request.",
            mismatches=mismatches,
            receipt_method=claimed_method,
            expected_method=expected_method.upper(),
            expected_url_sha256=actual_url_hash,
            receipt_url_sha256=claimed_url_hash,
            expected_params_sha256=actual_params_hash,
            receipt_params_sha256=claimed_params_hash,
        )
    return _verdict(
        "VERIFIED",
        "Method, exact URL bytes, and exact serialized parameter bytes match the request hashes in the receipt.",
        method=claimed_method,
        url_sha256=actual_url_hash,
        params_sha256=actual_params_hash,
    )


def _chain_evidence(tx_hash: str) -> dict[str, Any]:
    last_error: str | None = None
    for endpoint in BASE_RPC_URLS:
        try:
            observation = fetch_base_rpc_evidence(tx_hash, endpoint, timeout=3.5)
            head_raw = fetch_json_rpc(endpoint, "eth_blockNumber", [], timeout=3.5)
            if not isinstance(head_raw, str) or not head_raw.startswith("0x"):
                raise ValueError("RPC returned invalid eth_blockNumber")
            return {
                "observation": observation,
                "current_block": int(head_raw, 16),
                "source_url": endpoint,
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {str(exc)[:180]}"
    raise RuntimeError(last_error or "all Base RPC endpoints failed")


def _verify_settlement(receipt: dict[str, Any], expected_tx: str, evidence: dict[str, Any] | None) -> dict[str, Any]:
    payment = receipt.get("payment") or {}
    receipt_tx = payment.get("tx_hash")
    if not isinstance(receipt_tx, str) or not TX_RE.fullmatch(receipt_tx):
        return _verdict("NOT_VERIFIED", "receipt.payment.tx_hash is invalid")
    if not TX_RE.fullmatch(expected_tx or ""):
        return _verdict("NOT_VERIFIED", "expected_transaction_hash is invalid")
    if receipt_tx.lower() != expected_tx.lower():
        return _verdict("NOT_VERIFIED", "Receipt transaction hash differs from the caller's expected transaction.", receipt_transaction_hash=receipt_tx)

    if int(payment.get("chain_id", 0)) != 8453:
        return _verdict("UNKNOWN", "First version independently verifies Base mainnet only.", chain_id=payment.get("chain_id"))
    asset_address = payment.get("asset_address")
    asset = str(payment.get("asset", ""))
    if asset_address:
        contract = str(asset_address)
    elif ADDR_RE.fullmatch(asset):
        contract = asset
    elif asset.lower() == "usdc":
        contract = BASE_NATIVE_USDC
    else:
        return _verdict("UNKNOWN", "Cannot resolve the receipt's token contract without guessing.", asset=asset)

    if contract.lower() != BASE_NATIVE_USDC.lower():
        return _verdict("UNKNOWN", "First version independently verifies Base mainnet USDC only.", asset_contract=contract)
    if not evidence:
        return _verdict("UNKNOWN", "Read-only Base transaction evidence could not be obtained.")

    observation = evidence.get("observation") or {}
    chain_tx = observation.get("chain_transaction") or {}
    transfer_data = observation.get("token_transfers") or {}
    transfers = transfer_data.get("items") if isinstance(transfer_data, dict) else []
    tx_status = str(chain_tx.get("status", "")).lower()
    block_value = chain_tx.get("block_number")
    try:
        block_number = int(block_value, 16) if isinstance(block_value, str) and block_value.startswith("0x") else int(block_value)
        confirmations = max(0, int(evidence["current_block"]) - block_number + 1)
    except (TypeError, ValueError, KeyError):
        return _verdict("UNKNOWN", "Could not determine confirmation count from the RPC response.")

    if tx_status != "success":
        if tx_status in {"reverted", "failed", "error", "dropped"}:
            return _verdict("NOT_VERIFIED", "The transaction did not succeed on Base.", chain_status=tx_status, confirmations=confirmations)
        return _verdict("UNKNOWN", "The chain transaction status is not a recognized terminal result.", chain_status=tx_status)

    payer = str(payment.get("payer", "")).lower()
    payee = str(payment.get("payee", "")).lower()
    raw_amount = str(payment.get("amount", ""))
    exact = [
        item for item in (transfers if isinstance(transfers, list) else [])
        if str(_field(item.get("from"), "hash")).lower() == payer
        and str(_field(item.get("to"), "hash")).lower() == payee
        and str(_field(item.get("token"), "address_hash")).lower() == contract.lower()
        and str(_field(item.get("total"), "value")) == raw_amount
    ]
    if len(exact) != 1:
        return _verdict(
            "NOT_VERIFIED",
            "The chain receipt does not contain exactly one USDC transfer matching receipt payer, payee, contract, and atomic amount.",
            matching_transfer_count=len(exact),
            chain_transfer_count=len(transfers) if isinstance(transfers, list) else 0,
            source_url=evidence.get("source_url"),
            confirmations=confirmations,
        )
    if confirmations < 2:
        return _verdict(
            "UNKNOWN",
            "The matching transfer is present but has fewer than two block confirmations.",
            confirmations=confirmations,
            source_url=evidence.get("source_url"),
        )
    return _verdict(
        "VERIFIED",
        "Independent Base RPC evidence matches the receipt's transaction, successful status, USDC contract, payer, payee, and exact atomic amount.",
        transaction_hash=receipt_tx,
        chain_id=8453,
        token_contract=contract,
        payer=payment.get("payer"),
        payee=payment.get("payee"),
        atomic_amount=raw_amount,
        confirmations=confirmations,
        source_url=evidence.get("source_url"),
    )


def audit_bundle(
    bundle: dict[str, Any],
    *,
    chain_loader: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    audited_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    receipt = bundle.get("receipt")
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be a JSON object")
    body_encoded = bundle.get("response_body_base64")
    if not isinstance(body_encoded, str) or not body_encoded:
        raise ValueError("response_body_base64 is required; submit exact raw response bytes encoded as base64")
    if len(body_encoded) > ((MAX_RESPONSE_BODY_BYTES + 2) // 3) * 4 + 8:
        raise ValueError("encoded response body exceeds the 128 KB limit")
    try:
        body_bytes = base64.b64decode(body_encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("response_body_base64 is invalid standard base64") from exc
    if len(body_bytes) > MAX_RESPONSE_BODY_BYTES:
        raise ValueError("raw response body exceeds the 128 KB limit")

    expected_signer = bundle.get("expected_seller_address")
    expected_tx = bundle.get("expected_transaction_hash")
    expected_url = bundle.get("expected_request_url")
    expected_method = bundle.get("expected_request_method")
    expected_params_json = bundle.get("expected_params_json", "{}")
    if not isinstance(expected_signer, str) or not ADDR_RE.fullmatch(expected_signer):
        raise ValueError("expected_seller_address must be a 20-byte EVM address")
    if not isinstance(expected_tx, str) or not TX_RE.fullmatch(expected_tx):
        raise ValueError("expected_transaction_hash must be a 32-byte transaction hash")
    if not isinstance(expected_url, str) or not expected_url.startswith("https://") or len(expected_url) > 2048:
        raise ValueError("expected_request_url must be the exact HTTPS request URL (including query string)")
    if not isinstance(expected_method, str) or not re.fullmatch(r"[A-Za-z]{3,10}", expected_method):
        raise ValueError("expected_request_method is invalid")
    if not isinstance(expected_params_json, str) or len(expected_params_json.encode("utf-8")) > 8192:
        raise ValueError("expected_params_json must be the exact serialized parameter string, at most 8 KB")

    # Validate payment fields before invoking RPC or typed-data recovery.
    payment = receipt.get("payment")
    request = receipt.get("request")
    response = receipt.get("response")
    if not all(isinstance(item, dict) for item in (payment, request, response)):
        raise ValueError("receipt must include payment, request, and response objects")
    if not isinstance(payment.get("chain_id"), int) or isinstance(payment.get("chain_id"), bool):
        raise ValueError("receipt.payment.chain_id must be an integer")
    if not ADDR_RE.fullmatch(str(payment.get("payer", ""))) or not ADDR_RE.fullmatch(str(payment.get("payee", ""))):
        raise ValueError("receipt payment payer/payee must be EVM addresses")
    if not isinstance(payment.get("amount"), str) or not payment["amount"].isdigit():
        raise ValueError("receipt.payment.amount must be an atomic-unit decimal string")
    if not isinstance(response.get("body_sha256"), str) or not HEX32_RE.fullmatch(response["body_sha256"]):
        raise ValueError("receipt.response.body_sha256 must be a 32-byte hex digest")

    body_hash = hashlib.sha256(body_bytes).hexdigest()
    receipt_body_hash = response["body_sha256"].lower().removeprefix("0x")
    if body_hash == receipt_body_hash:
        body_result = _verdict(
            "VERIFIED",
            "SHA-256 of the exact supplied response bytes matches receipt.response.body_sha256.",
            actual_body_sha256=body_hash,
            body_bytes=len(body_bytes),
        )
    else:
        body_result = _verdict(
            "NOT_VERIFIED",
            "Exact supplied response bytes do not match receipt.response.body_sha256.",
            actual_body_sha256=body_hash,
            receipt_body_sha256=receipt_body_hash,
            body_bytes=len(body_bytes),
        )

    signer_result = _verify_seller_signature(receipt, expected_signer)
    request_result = _verify_request_binding(receipt, expected_url, expected_method, expected_params_json)

    tx_hash = str(payment.get("tx_hash", ""))
    if tx_hash.lower() != expected_tx.lower():
        tx_binding = _verdict(
            "NOT_VERIFIED",
            "Signed receipt tx_hash differs from expected_transaction_hash.",
            receipt_transaction_hash=tx_hash,
            expected_transaction_hash=expected_tx,
        )
    else:
        tx_binding = _verdict(
            "VERIFIED",
            "The signed receipt transaction hash matches the caller-supplied expected transaction.",
            transaction_hash=tx_hash,
        )

    chain_result: dict[str, Any]
    if chain_loader is None:
        try:
            evidence = _chain_evidence(expected_tx)
            chain_result = _verify_settlement(receipt, expected_tx, evidence)
        except Exception as exc:
            chain_result = _verdict("UNKNOWN", f"Read-only Base RPC evidence unavailable: {type(exc).__name__}.")
    else:
        try:
            chain_result = _verify_settlement(receipt, expected_tx, chain_loader(expected_tx))
        except Exception as exc:
            chain_result = _verdict("UNKNOWN", f"Read-only Base RPC evidence unavailable: {type(exc).__name__}.")

    signed_body_binding = (
        _verdict("VERIFIED", "The trusted seller signature covers the receipt body hash, and the exact supplied bytes match that hash.")
        if signer_result.get("verdict") == "VERIFIED" and body_result.get("verdict") == "VERIFIED"
        else _verdict("NOT_VERIFIED", "The signature and response bytes did not both verify.")
        if signer_result.get("verdict") == "NOT_VERIFIED" or body_result.get("verdict") == "NOT_VERIFIED"
        else _verdict("UNKNOWN", "The signature or response-body hash is not verified.")
    )

    components = {
        "seller_signature": signer_result,
        "request_binding": request_result,
        "response_body_integrity": body_result,
        "signed_response_binding": signed_body_binding,
        "transaction_binding": tx_binding,
        "on_chain_settlement": chain_result,
        "seller_signer_matches_payee": _verdict(
            "VERIFIED" if str(signer_result.get("recovered_signer", "")).lower() == str(payment.get("payee", "")).lower() else "NOT_VERIFIED",
            "The recovered seller signer address is compared to the signed payment.payee field.",
            recovered_signer=signer_result.get("recovered_signer"),
            payment_payee=payment.get("payee"),
        ) if signer_result.get("verdict") == "VERIFIED" else _verdict("UNKNOWN", "Cannot compare signer to payee until the signature is verified."),
    }
    values = [item["verdict"] for item in components.values()]
    overall = "NOT_VERIFIED" if "NOT_VERIFIED" in values else "VERIFIED" if all(v == "VERIFIED" for v in values) else "UNKNOWN"
    return {
        "schema": "sable.x402.evidence-bundle-audit.v1",
        "audited_at_utc": audited_at,
        "payment_submitted": False,
        "remote_actions_performed": ["read-only Base RPC lookups for the supplied transaction hash"],
        "input_scope": {
            "receipt_scheme": receipt.get("scheme"),
            "network": "Base mainnet" if payment.get("chain_id") == 8453 else f"chain_id {payment.get('chain_id')}",
            "response_body_bytes": len(body_bytes),
            "response_body_sha256": body_hash,
            "request_method": expected_method.upper(),
            "expected_request_url_host": urlsplit(expected_url).hostname,
            "expected_transaction_hash": expected_tx,
        },
        "overall_verdict": overall,
        "components": components,
        "limitations": [
            "This audit validates a supplied evidence bundle; it cannot recover raw response bytes that the caller does not possess.",
            "The expected seller signer, exact request URL, serialized parameters, and expected transaction hash must come from a separate trusted context.",
            "Base mainnet USDC is the only chain/asset verified independently in this first version; unsupported assets stay UNKNOWN.",
            "A matching body digest proves byte integrity, not semantic correctness or genuine computation.",
            "A valid seller signature is not an independent witness or buyer acceptance."
        ],
    }


def _read_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_type = handler.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ValueError("Content-Type must be application/json")
    try:
        length = int(handler.headers.get("Content-Length", ""))
    except ValueError as exc:
        raise ValueError("A valid Content-Length header is required") from exc
    if length < 2 or length > MAX_REQUEST_BYTES:
        raise ValueError("Request must be between 2 bytes and 256 KB")
    raw = handler.rfile.read(length)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Request body must be valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("Request JSON must be an object")
    return value


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED"}, origin)
            return
        json_response(self, 200, {
            "schema": "sable.x402.evidence-bundle-audit.v1",
            "method": "POST",
            "payment_required": False,
            "supported_receipt_scheme": "x402-receipts/v0",
            "supported_network_asset": "Base mainnet USDC",
            "required_fields": [
                "receipt",
                "response_body_base64",
                "expected_seller_address",
                "expected_transaction_hash",
                "expected_request_url",
                "expected_request_method",
                "expected_params_json",
            ],
            "max_request_bytes": MAX_REQUEST_BYTES,
            "max_response_body_bytes": MAX_RESPONSE_BODY_BYTES,
            "scope": "verify seller EIP-712 signature, exact URL/params hashes, raw response bytes hash, and Base USDC settlement; missing or unsupported evidence stays UNKNOWN",
        }, origin)

    def do_POST(self):
        allowed, origin = origin_is_allowed(self)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED"}, origin)
            return
        try:
            bundle = _read_body(self)
            result = audit_bundle(bundle)
            json_response(self, 200, result, origin)
        except ValueError as exc:
            json_response(self, 400, {"error": "INVALID_EVIDENCE_BUNDLE", "message": str(exc)}, origin)
        except Exception as exc:
            json_response(self, 500, {"error": "EVIDENCE_BUNDLE_AUDIT_FAILED", "message": type(exc).__name__}, origin)

    def log_message(self, format, *args):
        return
