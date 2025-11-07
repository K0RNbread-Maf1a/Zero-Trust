# 2FA (Two-Factor Authentication)

This document explains the 2FA login flow for the web portal.

## Requirements
- An authenticator app (e.g., Google Authenticator, 1Password, Authy)
- Server has `pyotp` and (optional) `qrcode` for QR images

## Flow
1. User enters email + password (`POST /auth/login_password`)
   - If 2FA not enrolled: response includes `{ requires_2fa_enrollment, secret, otpauth_uri, qr_data_url? }`
     - User adds account to authenticator using the secret or QR
     - User verifies with code via `POST /2fa/enroll_verify { email, code }`
     - Then re-run `POST /auth/login_password`
   - If 2FA enrolled: response includes `{ two_factor_required, login_token }`
2. User enters one-time code from authenticator (`POST /auth/2fa_verify { login_token, code }`)
   - On success, the session is marked `logged_in=true`
3. If the session is also `paid=true`, the portal unlocks user services

## Endpoints
- `POST /auth/login_password` → step 1
- `POST /auth/2fa_verify` → step 2
- `POST /2fa/enroll_start` and `POST /2fa/enroll_verify` → enrollment helpers

## Session Flags
- `paid` – set by paywall (Stripe dev/prod)
- `logged_in` – set after successful 2FA verification
- `verified` – email verification flag from registration flow

## Security Notes
- Enforce HTTPS and set Secure cookies in production
- Consider server-side rate limits for 2FA attempts
- Store 2FA secrets encrypted at rest if using a DB
- You can enforce 2FA for all sessions by setting `FORCE_2FA=1` (default). When disabled (`FORCE_2FA=0`), paid access is allowed without the `logged_in` flag.
