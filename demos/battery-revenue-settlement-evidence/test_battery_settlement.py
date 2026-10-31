import json, unittest
from pathlib import Path
from battery_settlement import reconcile
ROOT=Path(__file__).parent
class BatterySettlementTests(unittest.TestCase):
 def load(self,name): return json.loads((ROOT/name).read_text(encoding="utf-8"))
 def test_contract_invoice_chain_variance(self):
  r=reconcile(self.load("sample_batch.json")); self.assertEqual(r["availability_pct"],"97.5000"); self.assertEqual(r["contract_penalty_usd"],"250.00"); self.assertEqual(r["expected_contract_payable"],"9750.00"); self.assertEqual(r["invoice_total"],"10000.00"); self.assertEqual(r["verdict"],"GAP"); self.assertIn("INVOICE_VS_CONTRACT_VARIANCE",{e["code"] for e in r["exceptions"]})
 def test_missing_meter_returns_unknown(self):
  r=reconcile(self.load("incomplete_batch.json")); self.assertEqual(r["verdict"],"UNKNOWN"); self.assertIsNone(r["expected_contract_payable"]); self.assertIn("MISSING_METER_INTERVALS",{e["code"] for e in r["exceptions"]})
 def test_duplicate_meter_blocks_calculation(self):
  b=self.load("sample_batch.json"); b["meter_intervals"].append(dict(b["meter_intervals"][0])); r=reconcile(b); self.assertEqual(r["verdict"],"UNKNOWN"); self.assertIn("DUPLICATE_METER_INTERVAL",{e["code"] for e in r["exceptions"]})
 def test_duplicate_settlement_line_not_double_counted(self):
  b=self.load("sample_batch.json"); b["settlement_lines"].append(dict(b["settlement_lines"][0])); r=reconcile(b); self.assertEqual(r["settlement_total"],"10000.00"); self.assertIn("SETTLEMENT_DUPLICATE",{e["code"] for e in r["exceptions"]})
 def test_currency_mismatch_not_summed(self):
  b=self.load("sample_batch.json"); b["payment_records"][0]["currency"]="EUR"; r=reconcile(b); self.assertIsNone(r["payment_total"]); self.assertEqual(r["verdict"],"UNKNOWN"); self.assertIn("PAYMENT_CURRENCY_MISMATCH",{e["code"] for e in r["exceptions"]})
if __name__=="__main__": unittest.main(verbosity=2)
