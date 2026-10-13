"""Free, read-only SABLE audit of the public x402-receipts pass vector."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any

from api.common import allowed_origins, json_response, method_not_allowed, origin_is_allowed
from scripts.sable_x402_collect import (
    BASE_NATIVE_USDC,
    BASE_RPC_URLS,
    fetch_base_rpc_evidence,
    fetch_json_rpc,
)

TX = "0xdeb5872c039a88ae37b66ae490c0c8da9b6a4c652d84494ddcc9a05211d6cc80"
PAYER = "0xe61bd34fcedf14e0b41b582166eed69e3a6def89"
PAYEE = "0x32d711c66dd1ad0c42d0cfe48e58ee5f2de7c243"
VECTOR_SIGNER = "0xc49adc1ef48fc1d237d55379fef7f3142ce22468"
TOKEN = BASE_NATIVE_USDC
RAW_AMOUNT = "5000"
SAMPLE_RECEIPT_URL = "https://github.com/StelarDigital/x402-receipts/blob/main/vectors/pass-settled-delivered.json"
VECTOR_NOTES_URL = "https://github.com/StelarDigital/x402-receipts/blob/main/vectors/VECTORS.md"


def audit_public_vector() -> dict[str, Any]:
    """Re-check the public fixture's on-chain settlement; keep receipt claims separate."""
    observed: dict[str, Any] | None = None
    rpc_errors: list[str] = []
    for endpoint in BASE_RPC_URLS:
        try:
            observed = fetch_base_rpc_evidence(TX, endpoint, timeout=1.75)
            break
        except Exception as exc:
            rpc_errors.append(f"{endpoint}: {type(exc).__name__}: {str(exc)[:180]}")
    if observed is None:
        return {
            "schema": "sable.x402.public-receipt-audit.v1",
            "sample": "StelarDigital/x402-receipts pass-settled-delivered",
            "sample_receipt_url": SAMPLE_RECEIPT_URL,
            "vector_notes_url": VECTOR_NOTES_URL,
            "audited_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "payment_required": False,
            "payment_submitted": False,
            "chain_query_performed": True,
            "overall_verdict": "UNKNOWN",
            "components": {
                "settlement_fields": {"verdict": "UNKNOWN", "reason": "Could not fetch the public Base transaction and receipt from the configured read-only RPC endpoints."},
                "settlement_finality": {"verdict": "UNKNOWN", "reason": "No usable chain receipt was available."},
                "receipt_signer_identity": {"verdict": "NOT_VERIFIED", "reason": "The upstream vector documents its signing key as a vector-only test key, not the production payee key."},
                "response_body_integrity": {"verdict": "UNKNOWN", "reason": "The fixture does not include the raw response body bytes needed to recompute body_sha256."},
                "buyer_acceptance": {"verdict": "UNKNOWN", "reason": "The sample has no buyer countersignature."},
            },
            "source_errors": rpc_errors,
        }

    chain_tx = observed["chain_transaction"]
    transfer_items = observed["token_transfers"].get("items", [])
    matching = [
        item for item in transfer_items
        if str((item.get("from") or {}).get("hash", "")).lower() == PAYER
        and str((item.get("to") or {}).get("hash", "")).lower() == PAYEE
        and str(((item.get("token") or {}).get("address_hash", ""))).lower() == TOKEN.lower()
        and str(((item.get("total") or {}).get("value", ""))) == RAW_AMOUNT
    ]
    settlement_status = str(chain_tx.get("status", "unknown")).lower()
    if settlement_status == "success" and len(matching) == 1:
        settlement_fields = {
            "verdict": "VERIFIED",
            "reason": "Read-only Base RPC receipt matches the vector's transaction hash, successful status, USDC contract, payer, payee, and exact atomic amount.",
            "transaction_hash": TX,
            "network": "eip155:8453",
            "payer": PAYER,
            "payee": PAYEE,
            "asset_contract": TOKEN,
            "atomic_amount": RAW_AMOUNT,
            "source_url": observed["chain_transaction"].get("source_url"),
        }
    elif settlement_status == "reverted" or len(matching) == 0:
        settlement_fields = {
            "verdict": "NOT_VERIFIED",
            "reason": "The public chain receipt does not establish the exact expected transfer.",
            "chain_status": settlement_status,
            "matching_transfer_count": len(matching),
            "source_url": observed["chain_transaction"].get("source_url"),
        }
    else:
        settlement_fields = {
            "verdict": "UNKNOWN",
            "reason": "Chain receipt is incomplete or has ambiguous matching transfer logs.",
            "chain_status": settlement_status,
            "matching_transfer_count": len(matching),
            "source_url": observed["chain_transaction"].get("source_url"),
        }

    finality = {"verdict": "UNKNOWN", "reason": "Could not check current Base block height for confirmations."}
    current_block: int | None = None
    receipt_block: int | None = None
    provider = str(observed.get("chain_rpc_observation", {}).get("provider", ""))
    receipt_block_raw = chain_tx.get("block_number")
    try:
        if isinstance(receipt_block_raw, str) and receipt_block_raw.startswith("0x"):
            receipt_block = int(receipt_block_raw, 16)
        elif isinstance(receipt_block_raw, int):
            receipt_block = receipt_block_raw
        head_raw = fetch_json_rpc(provider, "eth_blockNumber", [], timeout=1.75) if provider else None
        if isinstance(head_raw, str) and head_raw.startswith("0x") and receipt_block is not None:
            current_block = int(head_raw, 16)
            confirmations = max(0, current_block - receipt_block + 1)
            if confirmations >= 2 and settlement_status == "success" and len(matching) == 1:
                finality = {
                    "verdict": "VERIFIED",
                    "reason": "The transaction is successful and has at least two block confirmations on Base.",
                    "confirmations": confirmations,
                    "block_number": receipt_block,
                    "current_block": current_block,
                    "source_url": provider,
                }
            elif settlement_status != "success":
                finality = {"verdict": "NOT_VERIFIED", "reason": "The transaction receipt is not successful.", "confirmations": confirmations}
            else:
                finality = {"verdict": "UNKNOWN", "reason": "The transaction has fewer than two confirmations.", "confirmations": confirmations}
    except Exception as exc:
        finality = {"verdict": "UNKNOWN", "reason": f"Could not determine confirmations: {type(exc).__name__}."}

    # The upstream conformance-vector documentation explicitly labels VECTOR_SIGNER
    # as a disposable test key and says it differs from the real payment payee.
    signer_match = VECTOR_SIGNER.lower() == PAYEE.lower()
    signer = {
        "verdict": "VERIFIED" if signer_match else "NOT_VERIFIED",
        "reason": "The vector signing address matches the on-chain payee." if signer_match else "Upstream vectors label this signature as a vector-only test key, not the production key; its signer address differs from payment.payee.",
        "vector_signer_address": VECTOR_SIGNER,
        "payment_payee": PAYEE,
        "source_url": VECTOR_NOTES_URL,
        "signature_verification_note": "This compatibility audit does not claim a production seller signature is authentic; the public vector uses a test-only signer.",
    }
    body = {
        "verdict": "UNKNOWN",
        "reason": "The vector supplies a body_sha256 claim but not the raw response body bytes, so SABLE cannot recompute the response digest.",
        "claimed_body_sha256": "5545e4424324ee42fd5b739544f462a47b81f122b02ec859af986e9316fadee4",
        "receipt_http_status": 200,
    }
    buyer = {
        "verdict": "UNKNOWN",
        "reason": "The vector has buyer.countersig = null; there is no cryptographic buyer acceptance in this fixture.",
    }

    parts = [settlement_fields["verdict"], finality["verdict"], signer["verdict"], body["verdict"], buyer["verdict"]]
    overall = "NOT_VERIFIED" if "NOT_VERIFIED" in parts else ("VERIFIED" if all(v == "VERIFIED" for v in parts) else "UNKNOWN")
    return {
        "schema": "sable.x402.public-receipt-audit.v1",
        "sample": "StelarDigital/x402-receipts pass-settled-delivered",
        "sample_receipt_url": SAMPLE_RECEIPT_URL,
        "vector_notes_url": VECTOR_NOTES_URL,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "payment_required": False,
        "payment_submitted": False,
        "chain_query_performed": True,
        "overall_verdict": overall,
        "components": {
            "settlement_fields": settlement_fields,
            "settlement_finality": finality,
            "receipt_signer_identity": signer,
            "response_body_integrity": body,
            "buyer_acceptance": buyer,
        },
        "limitations": [
            "This is a public conformance-vector audit, not a buyer-specific paid report.",
            "The upstream vector intentionally uses a vector-only seller key, so it is not a production seller identity attestation.",
            "Raw response-body bytes are absent; the body hash cannot be independently recomputed.",
            "A seller-signed receipt is not an independent witness and does not prove semantic correctness.",
            "No paid endpoint was called and no payment was submitted.",
        ],
        "chain_rpc_observation": observed.get("chain_rpc_observation"),
        "source_errors": rpc_errors,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed, origin = origin_is_allowed(self, allow_missing=True)
        if not allowed:
            json_response(self, 403, {"error": "ORIGIN_NOT_ALLOWED", "message": "This demo origin is not approved."}, origin)
            return
        try:
            json_response(self, 200, audit_public_vector(), origin)
        except Exception:
            json_response(self, 502, {"error": "PUBLIC_RECEIPT_AUDIT_UNAVAILABLE", "message": "The read-only public receipt audit could not complete. No payment was taken."}, origin)

    def do_POST(self):
        method_not_allowed(self, "GET")

    def log_message(self, format, *args):
        return
