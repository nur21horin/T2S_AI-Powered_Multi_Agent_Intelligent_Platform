# Authentication security

## Credentials and accounts

- Passwords are hashed with Argon2id; plaintext passwords are never stored.
- Public registration always assigns `STUDENT`. The request schema has no
  writable role field. Teacher, alumni, and administrator provisioning is not
  part of Step 2.
- Email addresses are normalized to lowercase and protected by a database
  uniqueness constraint and lowercase check constraint.
- Users must be active and email-verified to log in, refresh, or use the
  authenticated current-user dependency.
- Invalid login responses do not distinguish unknown, unverified, inactive, or
  wrong-password accounts. Password recovery uses a generic response.

## Access and refresh tokens

- Access credentials are signed JWTs with a fixed HS256 algorithm, issuer,
  audience, subject, token type, issue/expiry times, and a unique token ID.
- Production requires a `JWT_SECRET_KEY` of at least 32 bytes. Keep all secrets
  in environment configuration; never place them in source control.
- Access JWTs are short-lived (15 minutes by default) and returned in the JSON
  response for Bearer use. The backend does not put access tokens in cookies.
- Refresh tokens are random opaque values. Only SHA-256 hashes are stored in
  `auth_tokens`. Refresh consumes the prior row atomically, issues a replacement
  within the same token family, and revokes the family if a consumed token is
  reused. Logout revokes the family.
- One-time verification and password-reset tokens are high-entropy, stored as
  hashes, expire, and can only be consumed once.
- Logout, password change, and reset revoke refresh tokens. Already-issued
  access JWTs remain usable until their short expiry unless the account is
  deactivated; Step 2 does not add an access-token denylist.

## Cookie and CSRF protections

- Refresh tokens use an HttpOnly cookie. `Secure` is forced in production and
  when `SameSite=None` is selected. SameSite, cookie name, domain, and path are
  configurable. The default path is `/api/v1/auth`.
- A separate signed CSRF cookie is paired with the `X-CSRF-Token` request
  header. Refresh and logout require a valid pair and an exact `Origin` match in
  `CORS_ALLOWED_ORIGINS`; SameSite is an additional browser control, not the
  only CSRF defense.
- Login also checks the request origin because it establishes the refresh
  cookie. Browser clients must send credentials for refresh/logout and use the
  CSRF token returned by login/refresh. After a page reload, obtain the current
  CSRF token from `GET /api/v1/auth/csrf`.
- Do not store access or refresh tokens in `localStorage`. Keep the access token
  in application memory and let the browser manage the HttpOnly refresh cookie.

## Email workflows

- SMTP delivery is optional at application startup but required for
  registration, verification resend, and password recovery. Those operations
  fail with a safe service-unavailable response if delivery is not configured;
  the API does not claim an email was sent.
- Configure `SMTP_HOST`, `SMTP_PORT`, `EMAIL_FROM`, `FRONTEND_BASE_URL`, and
  either STARTTLS or implicit TLS. Production rejects explicitly insecure SMTP
  transport. SMTP credentials are optional and remain secret-valued settings.
- Automated tests inject a fake sender and never send real messages.

## Step 2 boundaries and remaining protections

Step 2 implements authentication only. RBAC, role/permission dependencies,
business-resource ownership/IDOR checks, general login and API rate limiting,
shared Redis controls, and broader security-event audit coverage are deferred
to Step 3. Login and email endpoints therefore still require application-wide
rate limiting before production exposure. Access-token revocation is also
bounded by the configured access-token lifetime.

See `API_CONTRACT_AUTH.md` for the frontend request and cookie contract.
