#!/usr/bin/env python3
"""Guard the buyer-facing SABLE offer against pricing and evidence-boundary drift."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class CommercialSurfaceTests(unittest.TestCase):
    def test_primary_buy_page_leads_with_micro_closure(self):
        page = read("buy/index.html")
        self.assertLess(page.index("$99"), page.index("$299"))
        self.assertIn("Did the action actually produce the result?", page)
        self.assertIn("https://paypal.me/tang665/99USD", page)
        self.assertIn("https://paypal.me/tang665/299USD", page)
        self.assertIn("PRODUCT=MICRO_CLOSURE", page)
        self.assertIn("PRODUCT=DECISION_CLOSURE", page)
        self.assertIn("Scope%20fit%20for%20one%20bounded%20SABLE%20check", page)
        self.assertIn("Payment starts intake", page)
        self.assertIn("scope and authorization must be confirmed before execution", page.lower())
        self.assertIn("micro-closure-receipt.md", page)

    def test_docs_buy_page_has_both_offers_and_scope_fit_path(self):
        page = read("docs/buy/index.html")
        self.assertIn("https://paypal.me/tang665/99USD", page)
        self.assertIn("https://paypal.me/tang665/299USD", page)
        self.assertIn("PRODUCT=MICRO_CLOSURE", page)
        self.assertIn("PRODUCT=DECISION_CLOSURE", page)
        self.assertIn("Scope%20fit%20for%20one%20bounded%20SABLE%20check", page)

    def test_buyer_card_requires_authorized_boundary_and_protects_secrets(self):
        card = read("docs/buy/SABLE_PAYMENT_CLOSURE_CARD_V1.md")
        for field in ("PRODUCT:", "CLAIM:", "REFERENCE:", "BOUNDARY:", "DECISION:"):
            self.assertIn(field, card)
        self.assertIn("Do not send credentials", card)
        normalized_card = card.replace("**", "").lower()
        self.assertIn("payment starts intake; it does not authorize production access or a production write", normalized_card)
        self.assertIn("before execution", normalized_card)
        self.assertIn("personal customer data", normalized_card)
        self.assertIn("private keys", normalized_card)
        self.assertIn("VERIFIED", card)
        self.assertIn("NOT_VERIFIED", card)
        self.assertIn("UNKNOWN", card)

    def test_offer_documents_use_the_same_two_prices(self):
        for path in (
            "COMMERCIAL_OFFER.md",
            "docs/COMMERCIAL_OFFER.md",
            "docs/COMMERCIAL_INDEPENDENT_VERIFICATION.md",
        ):
            with self.subTest(path=path):
                offer = read(path)
                self.assertIn("US$99", offer)
                self.assertIn("US$299", offer)
                self.assertIn("https://paypal.me/tang665/99USD", offer)
                self.assertIn("https://paypal.me/tang665/299USD", offer)
                self.assertIn("PRODUCT=MICRO_CLOSURE", offer)
                self.assertIn("PRODUCT=DECISION_CLOSURE", offer)

    def test_readme_has_one_consolidated_buying_section(self):
        readme = read("README.md")
        self.assertEqual(readme.count("## Buy the bounded check"), 1)
        self.assertIn("confirm scope fit", readme)
        self.assertIn("Payment starts intake", readme)
        self.assertIn("PRODUCT=MICRO_CLOSURE", readme)
        self.assertIn("PRODUCT=DECISION_CLOSURE", readme)

    def test_ai_buyer_offers_have_distinct_payment_product_codes(self):
        page = read("buy/index.html")
        for code in ("PRODUCT=AI_BUYER_CHECK", "PRODUCT=AI_BUYER_REALITY"):
            with self.subTest(code=code):
                self.assertIn(code, page)
        self.assertIn("public website URL", page)
        self.assertIn("changed page/revision", page)

    def test_receipt_example_never_masquerades_as_customer_evidence(self):
        receipt = read("examples/micro-closure-receipt.md")
        self.assertIn("SYNTHETIC EXAMPLE ONLY", receipt)
        self.assertIn("not a real payment", receipt)
        self.assertIn("does not establish production readiness", receipt)
        self.assertIn("UNKNOWN", receipt)


if __name__ == "__main__":
    unittest.main()
