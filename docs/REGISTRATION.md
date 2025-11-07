# Customer Registration

This document describes the registration and verification flow for customers.

## Flow
1. Start registration: POST `/register/start` with `{ email, password }`
2. Receive a verification code (via email in production; returned in dev mode)
3. Verify: POST `/register/verify` with `{ email, code }`
4. Login (optional): POST `/register/login` with `{ email, password }`

After verification, the session is associated with the `customer_id` and marked `verified=true`.

## API
- POST `/register/start`
  - Request: `{ email: string, password: string }`
  - Response: `{ success: boolean, message: string, code?: string }`
  - Env: `RETURN_VERIFICATION_CODE=1` to include `code` in response (dev only)

- POST `/register/verify`
  - Request: `{ email: string, code: string }`
  - Response: `{ success: boolean, customer_id: string }`

- POST `/register/login`
  - Request: `{ email: string, password: string }`
  - Response: `{ success: boolean, customer_id: string, verified: boolean }`

## Storage
- In-memory by default; use Redis by setting `REDIS_URL`
- Pending registration TTL (Redis): 1 hour

## Email Templates
- `web/templates/email_verification.txt`
  - Render `{{ code }}` with your mailer
