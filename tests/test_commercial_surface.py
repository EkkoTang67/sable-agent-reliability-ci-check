#!/usr/bin/env python3
"""Guard the buyer-facing SABLE offer against pricing and evidence-boundary drift."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class CommercialSurfaceTests(unittest.TestCase):
    def test_primary_buy_page_has_one_focused_pretest_readiness_offer(self):
        page = read("buy/index.html")
        self.assertIn("Before the test window, prove the evidence package is ready.", page)
        self.assertIn("US$2,500", page)
        self.assertIn("https://paypal.me/tang665/2500USD", page)
        self.assertIn("PRODUCT=PRETEST_READINESS_AUDIT", page)
        self.assertIn("one authorized commissioning subsystem", page)
        self.assertIn("source-linked evidence graph", page)
        self.assertIn("If a safe mutually agreed scope cannot be established within five business days", page)
        self.assertIn("does not automatically determine whether a generic or public requirement applies", page.lower())
        self.assertIn("explicitly open issues", page)
        self.assertIn("No facility access", page)
        self.assertIn("https://igchicago.org/wp-content/uploads/2023/08/OIG-Audit-of-the-PBCs-Administration-of-Building-Commissioning.pdf", page)
        self.assertIn("Do not attach project files", page)
        self.assertNotIn("https://paypal.me/tang665/99USD", page)
        self.assertNotIn("https://paypal.me/tang665/299USD", page)
        self.assertNotIn("PRODUCT=AI_BUYER_CHECK", page)
        self.assertNotIn("PRODUCT=AI_BUYER_REALITY", page)

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

    def test_primary_checkout_does_not_mix_unrelated_products(self):
        page = read("buy/index.html")
        self.assertNotIn("AI Buyer Readiness", page)
        self.assertNotIn("PRODUCT=AI_BUYER_CHECK", page)
        self.assertNotIn("PRODUCT=AI_BUYER_REALITY", page)

    def test_receipt_example_never_masquerades_as_customer_evidence(self):
        receipt = read("examples/micro-closure-receipt.md")
        self.assertIn("SYNTHETIC EXAMPLE ONLY", receipt)
        self.assertIn("not a real payment", receipt)
        self.assertIn("does not establish production readiness", receipt)
        self.assertIn("UNKNOWN", receipt)


if __name__ == "__main__":
    unittest.main()
