"""Regression tests for read-only Base RPC fallback and conservative verdicts."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from sable_x402_collect import BASE_NATIVE_USDC, TRANSFER_TOPIC, fetch_base_rpc_evidence, normalize_live_case, normalized_amount  # noqa: E402
from sable_x402_closure import assess  # noqa: E402

TX = "0x" + "ab" * 32
RECIPIENT = "0x367f1b3d8ca90d1e087481a9a40d585bf3451a03"
SENDER = "0x" + "11" * 20


def topic_address(address):
    return "0x" + ("0" * 24) + address[2:].lower()


class BaseRpcFallbackTests(unittest.TestCase):
    def fixture(self):
        receipt = {
            "transactionHash": TX,
            "status": "0x1",
            "blockNumber": "0x1234",
            "logs": [{
                "address": BASE_NATIVE_USDC,
                "topics": [TRANSFER_TOPIC, topic_address(SENDER), topic_address(RECIPIENT)],
                "data": hex(50_000),
            }],
        }
        return {
            "eth_chainId": "0x2105",
            "eth_getTransactionByHash": {"hash": TX},
            "eth_getTransactionReceipt": receipt,
        }

    def test_rpc_receipt_normalizes_usdc_transfer_and_stays_conservative(self):
        replies = self.fixture()
        def fake_rpc(url, method, params, timeout):
            return replies[method]
        sources = fetch_base_rpc_evidence(TX, "https://mainnet.base.org", rpc_call=fake_rpc)
        self.assertEqual(sources["chain_transaction"]["status"], "success")
        transfers = sources["token_transfers"]["items"]
        self.assertEqual(len(transfers), 1)
        self.assertEqual(normalized_amount(transfers[0]), "0.05")
        self.assertEqual(transfers[0]["to"]["hash"], RECIPIENT)
        dossier = normalize_live_case(
            tx_hash=TX, slug="feeds", expected_amount="0.05", recipient=RECIPIENT,
            asset="USDC", asset_contract=BASE_NATIVE_USDC, endpoint="/feeds/api/query",
            network="eip155:8453", sources=sources, source_errors={}, response_receipt=None,
        )
        report = assess(dossier)
        self.assertEqual(report["components"]["settlement"]["verdict"], "VERIFIED")
        self.assertEqual(report["components"]["service_binding"]["verdict"], "UNKNOWN")
        self.assertEqual(report["components"]["delivery"]["verdict"], "UNKNOWN")
        self.assertEqual(report["overall_verdict"], "UNKNOWN")

    def test_wrong_chain_is_rejected(self):
        replies = self.fixture()
        replies["eth_chainId"] = "0x1"
        def fake_rpc(url, method, params, timeout):
            return replies[method]
        with self.assertRaisesRegex(ValueError, "unexpected chain ID"):
            fetch_base_rpc_evidence(TX, "https://mainnet.base.org", rpc_call=fake_rpc)

    def test_mismatched_transaction_hash_is_rejected(self):
        replies = self.fixture()
        replies["eth_getTransactionByHash"] = {"hash": "0x" + "cd" * 32}
        def fake_rpc(url, method, params, timeout):
            return replies[method]
        with self.assertRaisesRegex(ValueError, "did not match"):
            fetch_base_rpc_evidence(TX, "https://mainnet.base.org", rpc_call=fake_rpc)


if __name__ == "__main__":
    unittest.main()
