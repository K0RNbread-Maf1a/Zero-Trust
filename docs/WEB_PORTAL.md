# Web Portal

This document describes the paywalled web portal, endpoints, and configuration.

## Overview
- UI served from `/app` and static assets under `/web`
- Customer registration with email verification
- Paywall via Stripe Checkout or dev simulation
- Session cookie `session_id` identifies a browser session

## Endpoints
- Public
  - GET `/app` – sets a session cookie and redirects to the UI
  - GET `/web/*` – static assets
- GET `/pay/config` – returns feature flags and Stripe configuration (includes `force_2fa`)
  - GET `/pay/status` – returns `{ paid, verified, customer_id }` for current session

- Registration
  - POST `/register/start` – body `{ email, password }`, returns `{ success, message, code? }`
    - In dev, `code` is returned if `RETURN_VERIFICATION_CODE=1`
  - POST `/register/verify` – body `{ email, code }`, returns `{ success, customer_id }`
  - POST `/register/login` – body `{ email, password }`, returns `{ success, customer_id, verified }`

- Stripe
  - POST `/pay/create-checkout-session` – returns `{ url }` to redirect the browser to Stripe Checkout
  - POST `/pay/webhook` – Stripe webhook (use `stripe listen` for local dev)
  - GET `/pay/stripe/success`, GET `/pay/stripe/cancel` – result pages

- Paywalled APIs (require paid session)
  - Files: `/api/files/*`
  - DB: `/api/database/*`
  - Users, API Keys

## Configuration
- STRIPE_SECRET_KEY – Stripe secret API key
- STRIPE_PRICE_ID – Price ID (e.g., `price_123`)
- STRIPE_WEBHOOK_SECRET – Webhook signing secret
- STRIPE_MODE – `payment` or `subscription` (default: `payment`)
- ENABLE_DEV_PAY – `1` to enable dev simulate; `0` to disable
- RETURN_VERIFICATION_CODE – `1` to return verification code from `/register/start`
- REDIS_URL – if set, sessions and registration use Redis
- SESSION_TTL – session TTL seconds (default 604800)

## Local dev
- Start server, then:
  ```powershell
  stripe listen --forward-to localhost:8000/pay/webhook
  ```
- Visit `http://localhost:8000/app`
- Use the Registration panel to create and verify an account
- Subscribe via Stripe or use Dev Simulate Payment

## Templates
- `web/checkout_success.html`, `web/checkout_cancel.html`
- `web/templates/email_verification.txt` – email body template
