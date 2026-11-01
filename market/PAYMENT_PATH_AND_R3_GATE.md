# SABLE payment-path gate — 2026-10-11

## Goal
Collect the first lawful paid pilot without waiting for a custom PayPal API integration. Use the seller's existing PayPal.Me route only if the seller account is eligible and the link works for commercial transactions.

## Publicly verified facts
- PayPal's Mainland China Worldwide Terms state that its service for Mainland China residents includes accepting and receiving payments, subject to the applicable China User Agreement and PayPal terms: https://www.paypal.cn/portal/paypal-worldwide-services-terms-and-conditions?locale.x=en&nav_active_index=6
- PayPal's China Help Center says personal users can add a personal bank account for RMB transfers, while business users may add company or legal-person personal bank accounts: https://www.paypal.cn/portal/help/article/362?locale.x=en
- Published PayPal seller fees for Mainland China list international commercial receiving transactions at 4.40% plus a fixed fee based on currency (USD fixed fee shown as $0.30): https://www.paypal.com/c2/business/paypal-business-fees
- PayPal's Worldwide Terms say withdrawals can be delayed or limited and fees/options are account-dependent; this must be checked in the seller's own account. Do not assume any individual account is KYC-complete or withdrawable.

## Practical no-API close path
1. Before asking for payment, confirm the exact scope, exclusions, acceptance criteria, delivery window, data handling and refund/cancellation terms in writing.
2. If buyer confirms they want the pilot, share the seller's existing PayPal.Me link with the agreed amount (goods/services transaction; never ask for friends/family payments).
3. Do not ask the buyer to put secrets or personal/customer data in a PayPal note.
4. Check the PayPal activity directly; reconcile payer, amount, currency, transaction ID, status, and any hold or limitation. A screenshot or buyer statement alone is not payment evidence.
5. Start work only after the agreed payment is completed and the funds are available under the seller's account terms, and after scope/data permissions are confirmed.
6. Record the payment receipt and evidence of settlement in the R3 ledger. If money is pending, held, refunded, reversed, or unwithdrawable, do not mark R3.
7. After service delivery, preserve the agreed deliverable, acceptance result and relevant records for normal tax/accounting compliance.

## Indicative gross-to-fee math, not final proceeds
If the published 4.40% + $0.30 USD fee applies to the exact transaction:
- $1,500 payment → estimated payment-processing fee $66.30, before withdrawal/conversion fees and tax.
- $2,500 payment → estimated payment-processing fee $110.30, before withdrawal/conversion fees and tax.

The applicable fee is determined by the account and transaction's current terms; check the account's own fee disclosure before pricing a real order.

## Hard unknowns that remain
- Whether the seller's exact PayPal.Me profile is currently active and can receive this type of international commercial payment.
- Whether the seller's account is fully verified and free of limitations or holds.
- The available withdrawal method, minimum amount, fee and timing for the seller's specific linked bank.
- Whether a specific high-ticket payer can pay through the available route.
- The seller's own tax/reporting treatment for each transaction.

Do not claim that a payment route is verified until the seller has inspected these account-specific conditions or a real buyer payment has completed.
Do not build custom checkout APIs or publish live checkout buttons merely to bypass these unknowns.

## Current state
- Existing PayPal.Me URL is known: https://paypal.me/tang665
- Payment route is plausible based on public PayPal terms but **not yet verified against the seller's live account or a completed transaction**.
- No invoice/order or settled funds from the new outreach are recorded.
- R3 remains unchanged.
