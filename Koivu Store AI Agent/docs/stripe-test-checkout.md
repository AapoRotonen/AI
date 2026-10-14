# Optional Stripe test checkout

This integration is for a local portfolio demo only. It accepts Stripe test-mode secret keys (`sk_test_...`), rejects live secret keys, and never creates real fulfillment. Do not enter a real card number. Use only a test number published in [Stripe's testing guide](https://docs.stripe.com/testing).

## Configure locally

1. In the Stripe Dashboard, switch to test mode and copy a test-mode secret key. Keep it on the backend; never put it in `frontend/app-config.js` or commit it.
2. Start the app as described in the [README](../README.md). For the separate local frontend and API commands there, the browser origin is `http://127.0.0.1:5500` and the API listens on port `8000`.
3. Install and authenticate Stripe CLI, then forward test events to the local API:

   ```powershell
   stripe listen --forward-to http://127.0.0.1:8000/payments/webhook
   ```

   The CLI prints a webhook signing secret beginning with `whsec_`. Use the secret for this running listener; it is distinct from the Stripe API key.
4. Set these values in `backend/.env` and restart the API:

   ```dotenv
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   PUBLIC_APP_URL=http://127.0.0.1:5500
   ```

   If the API itself serves the website at port `8000`, use `http://127.0.0.1:8000` as `PUBLIC_APP_URL` instead.
5. Sign in, add a sample product to the cart, and choose **Avaa testikassa**. Stripe Checkout runs in test mode. A verified event updates the account's synthetic order; returning from Checkout alone does not mark it paid.

Checkout stays hidden unless all three settings are present. Removing them and restarting the API disables it. The app sends Stripe the sample product names, quantities, prices, and synthetic order/account references. Card details are entered on Stripe's hosted page. The webhook signature is checked over the exact raw request body before order state changes.

## Azure status

The current Azure deployment workflow does not pass Stripe credentials or webhook configuration to Container Apps. Test checkout therefore remains disabled on the deployed site. Do not add Stripe credentials to public config, Bicep parameters/outputs, or deployment logs. Enabling a cloud test checkout requires a separately reviewed workflow and server-side secret configuration; a live key must never be used for this demo.
