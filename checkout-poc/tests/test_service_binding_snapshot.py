"""Regression tests for binding service snapshot records to an exact transaction hash."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from sable_x402_collect import BASE_NATIVE_USDC, normalize_live_case  # noqa: E402
from sable_x402_closure import assess  # noqa: E402

TX = "0x" + "77" * 32
RECIPIENT = "0x367f1b3d8ca90d1e087481a9a40d585bf3451a03"


class ServiceBindingSnapshotTests(unittest.TestCase):
    def base_case(self, capability_snapshot):
        return normalize_live_case(
            tx_hash=TX,
            slug="feeds",
            expected_amount="0.05",
            recipient=RECIPIENT,
            asset="USDC",
            asset_contract=BASE_NATIVE_USDC,
            endpoint="/feeds/api/query",
            network="eip155:8453",
            sources={"capability_snapshot": capability_snapshot},
            source_errors={},
            response_receipt=None,
        )

    def test_nested_hash_and_nested_valid_flag_are_preserved(self):
        dossier = self.base_case({
            "items": [{
                "hash": TX.upper().replace("0X", "0x"),
                "endpoint": "/feeds/api/query",
                "price_usd": "0.05",
                "valid": True,
                "match_score": 0.99,
            }]
        })
        report = assess(dossier)
        self.assertEqual(report["components"]["service_binding"]["verdict"], "VERIFIED")
        self.assertEqual(report["components"]["service_binding"]["scope"], "metadata_only")
        self.assertFalse(report["components"]["service_binding"]["independent_source"])
        self.assertEqual(report["components"]["delivery"]["verdict"], "UNKNOWN")
        self.assertEqual(report["overall_verdict"], "UNKNOWN")

    def test_unrelated_transaction_does_not_bind(self):
        dossier = self.base_case({
            "items": [{
                "hash": "0x" + "88" * 32,
                "endpoint": "/feeds/api/query",
                "price_usd": "0.05",
                "valid": True,
            }]
        })
        report = assess(dossier)
        self.assertEqual(report["components"]["service_binding"]["verdict"], "UNKNOWN")

    def test_matching_transaction_with_wrong_endpoint_is_not_verified(self):
        dossier = self.base_case({
            "items": [{
                "hash": TX,
                "endpoint": "/admin/delete",
                "price_usd": "0.05",
                "valid": True,
            }]
        })
        report = assess(dossier)
        self.assertEqual(report["components"]["service_binding"]["verdict"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
