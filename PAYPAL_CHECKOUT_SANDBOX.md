# PayPal Checkout — Sandbox Preview

This branch adds the SABLE order/capture/webhook routes and the purchase page. It deliberately disables direct PayPal.Me live-payment links in the preview. It is not a live-payment release.

## Required Vercel Preview variables

- `PAYPAL_ENV=sandbox`
- `PAYPAL_CLIENT_ID` — the sandbox app client ID
- `PAYPAL_CLIENT_SECRET` — the sandbox app secret
- `PAYPAL_MERCHANT_ID` — the sandbox seller merchant ID
- `PAYPAL_WEBHOOK_ID` — the webhook ID registered for this deployed preview URL

Do not commit or paste secrets into GitHub issues, PR comments, or chat. Add them only in Vercel Project Settings → Environment Variables and select **Preview** only for sandbox testing.

Create the webhook after a public preview URL is available, using `https://<preview-host>/api/paypal/webhook`. Check Vercel deployment protection: PayPal's webhook sender must be able to POST to that endpoint. Do not expose live credentials or enable real-money checkout as part of the sandbox test.

The checkout guard remains off unless credentials, merchant ID, webhook ID, and the environment mode all match. The capture handler is intended to issue a receipt only after a completed capture is independently read back and validated.

## Local check

Run `npm test` with Node.js 20+.
