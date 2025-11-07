# Paywall and Sessions

This document explains how sessions and the paywall work, and how to configure Stripe.

## Sessions
- A `session_id` cookie is set on first visit to `/app`
- Session data includes: `paid`, `customer_id`, `verified`, `created_at`
- Backend store is Redis if `REDIS_URL` is set, else in-memory
- TTL: `SESSION_TTL` (default 7 days)

## Payment options
- Stripe Checkout (recommended)
- Dev simulation (for local testing)

### Stripe configuration
- `STRIPE_SECRET_KEY`: Secret API key
- `STRIPE_PRICE_ID`: Price ID for the product/plan
- `STRIPE_WEBHOOK_SECRET`: Webhook signing secret (from `stripe listen` or dashboard)
- `STRIPE_MODE`: `payment` (one-time) or `subscription` (recurring)

### 2FA enforcement
- `FORCE_2FA`: `1` to require 2FA login (default), `0` to allow paid-only access

### Dev simulation toggle
- `ENABLE_DEV_PAY=1` enables POST `/pay/dev/complete` (default enabled)
- Set `ENABLE_DEV_PAY=0` to disable

## Checkout flow
1. Client calls `POST /pay/create-checkout-session`
2. Server creates a session with Stripe and returns the checkout URL
3. Client redirects to Stripe, completes payment
4. Stripe calls `/pay/webhook` with `checkout.session.completed`
5. Server marks `session.paid = true` using metadata `session_id`

## Security notes
- Always run behind HTTPS in production and set Secure cookies
- Use a durable session store (Redis)
- Never expose secrets in logs or to clients
- Limit webhook IPs or require signature verification (already implemented)
