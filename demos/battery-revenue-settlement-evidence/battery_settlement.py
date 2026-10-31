#!/usr/bin/env python3
"""Contract-driven battery revenue settlement evidence checker (synthetic demo only)."""
from __future__ import annotations
import argparse, json
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def D(value: Any) -> Decimal:
    return Decimal(str(value))

def reconcile(batch: dict[str, Any]) -> dict[str, Any]:
    contract = batch["contract"]
    asset, period, currency = contract["asset_id"], contract["period"], contract["currency"]
    exceptions: list[dict[str, str]] = []
    meter_rows = [r for r in batch.get("meter_intervals", []) if r.get("asset_id") == asset and r.get("period") == period]
    ids = [r.get("interval_id", "") for r in meter_rows]
    duplicates = sorted(k for k, v in Counter(ids).items() if k and v > 1)
    for interval_id in duplicates:
        exceptions.append({"code":"DUPLICATE_METER_INTERVAL","reference":interval_id,"severity":"HIGH"})
    unique_rows = {}
    for row in meter_rows:
        key = row.get("interval_id", "")
        if key and key not in unique_rows: unique_rows[key] = row
    required, received = int(contract["required_intervals"]), len(unique_rows)
    if received < required:
        exceptions.append({"code":"MISSING_METER_INTERVALS","reference":f"expected={required};received={received}","severity":"HIGH"})
    bad_quality = [r.get("interval_id","") for r in unique_rows.values() if r.get("quality") != "VALID"]
    for key in bad_quality:
        exceptions.append({"code":"METER_QUALITY_NOT_VALID","reference":key,"severity":"HIGH"})
    coverage_complete = received == required and not duplicates and not bad_quality
    expected_payable = availability_pct = penalty = None
    if coverage_complete:
        contracted_mw = D(contract["contracted_mw"])
        if contracted_mw <= 0: raise ValueError("contracted_mw must be positive")
        duration = sum((D(r["duration_hours"]) for r in unique_rows.values()), Decimal("0"))
        if duration <= 0: raise ValueError("total duration must be positive")
        available = sum((D(r["available_mw"])*D(r["duration_hours"]) for r in unique_rows.values()), Decimal("0"))
        availability_pct = available/(contracted_mw*duration)*Decimal("100")
        shortfall = max(Decimal("0"), D(contract["availability_target_pct"])-availability_pct)
        penalty = min(D(contract["max_penalty_usd"]), shortfall*D(contract["penalty_per_percentage_point_usd"]))
        expected_payable = max(Decimal("0"), D(contract["base_availability_payment_usd"])-penalty)
    else:
        exceptions.append({"code":"CONTRACT_PAYABLE_NOT_VERIFIABLE","reference":"meter evidence incomplete or duplicated","severity":"HIGH"})
    def total_unique(rows, id_field, amount_field, code):
        seen = {}
        for row in rows:
            if row.get("asset_id") != asset or row.get("period") != period: continue
            if row.get("currency") != currency:
                exceptions.append({"code":f"{code}_CURRENCY_MISMATCH","reference":str(row.get(id_field,"unknown")),"severity":"HIGH"}); continue
            key = str(row.get(id_field,""))
            if not key:
                exceptions.append({"code":f"{code}_MISSING_REFERENCE","reference":"missing id","severity":"MEDIUM"}); continue
            amount = D(row[amount_field])
            if key in seen:
                suffix = "DUPLICATE_CONFLICT" if seen[key] != amount else "DUPLICATE"
                severity = "HIGH" if suffix.endswith("CONFLICT") else "MEDIUM"
                exceptions.append({"code":f"{code}_{suffix}","reference":key,"severity":severity}); continue
            seen[key] = amount
        return sum(seen.values(), Decimal("0")) if seen else None
    invoice = total_unique(batch.get("invoice_lines",[]),"invoice_line_id","amount","INVOICE")
    settlement = total_unique(batch.get("settlement_lines",[]),"settlement_line_id","amount","SETTLEMENT")
    payment = total_unique(batch.get("payment_records",[]),"payment_id","amount","PAYMENT")
    if expected_payable is not None and invoice is not None and invoice != expected_payable:
        exceptions.append({"code":"INVOICE_VS_CONTRACT_VARIANCE","reference":f"invoice={money(invoice)};expected={money(expected_payable)};variance={money(invoice-expected_payable)} {currency}","severity":"HIGH"})
    if invoice is not None and settlement is not None and invoice != settlement:
        exceptions.append({"code":"SETTLEMENT_VS_INVOICE_VARIANCE","reference":f"settlement={money(settlement)};invoice={money(invoice)};variance={money(settlement-invoice)} {currency}","severity":"HIGH"})
    if settlement is not None and payment is not None and settlement != payment:
        exceptions.append({"code":"PAYMENT_VS_SETTLEMENT_VARIANCE","reference":f"paid={money(payment)};settled={money(settlement)};variance={money(payment-settlement)} {currency}","severity":"HIGH"})
    if expected_payable is None or invoice is None or settlement is None or payment is None: verdict="UNKNOWN"
    elif exceptions: verdict="GAP"
    else: verdict="PASS"
    return {
      "demo_notice":"Synthetic contract-driven illustration only; not ISO market settlement, trading advice, accounting assurance, or an audit opinion.",
      "batch_id":batch.get("batch_id","UNNAMED"),"asset_id":asset,"period":period,"currency":currency,"verdict":verdict,
      "meter_coverage":{"required_intervals":required,"unique_intervals":received,"duplicates":duplicates},
      "availability_pct":None if availability_pct is None else str(availability_pct.quantize(Decimal("0.0001"))),
      "contract_penalty_usd":None if penalty is None else money(penalty),
      "expected_contract_payable":None if expected_payable is None else money(expected_payable),
      "invoice_total":None if invoice is None else money(invoice),"settlement_total":None if settlement is None else money(settlement),
      "payment_total":None if payment is None else money(payment),"exceptions":exceptions}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch",type=Path); parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=reconcile(json.loads(args.batch.read_text(encoding="utf-8")))
    rendered=json.dumps(result,indent=2,ensure_ascii=False)
    if args.output: args.output.write_text(rendered+"\n",encoding="utf-8")
    print(rendered)

if __name__=="__main__": main()
