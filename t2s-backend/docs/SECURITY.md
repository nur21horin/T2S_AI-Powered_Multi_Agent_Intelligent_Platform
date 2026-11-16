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
  audience, subject, token type, issue/expiry times, a unique token ID, and
  `auth_version`. JWTs without a valid version are rejected.
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
- Logout, password change, and reset revoke refresh tokens. Password changes
  and resets atomically increment the user's `auth_version`, invalidating all
  previously issued access JWTs. Any future authorized role-change operation
  must update the role and call `UserRepository.increment_auth_version` in the
  same transaction; Step 3.1 adds no role modification operation.
- Logout accepts the current Bearer access token and stores only its `jti` in a
  Redis denylist. The key is namespaced and expires no later than the JWT. The
  Redis write happens before PostgreSQL refresh-family revocation. If Redis
  fails, logout returns HTTP 503 without changing the refresh family or clearing
  cookies; retry with the same credentials after Redis is restored. If Redis
  succeeds but PostgreSQL fails, the access token is revoked, the database
  transaction is rolled back, and logout returns HTTP 503. Retrying is safe:
  the Redis write is idempotent and the stored refresh-token row still provides
  its family ID even if that family was already revoked. Expired or invalid
  access tokens do not require a Redis write because they cannot authenticate;
  a valid refresh family can still be revoked. Omitting the Bearer token only
  revokes the refresh family, and any unpresented access token expires naturally.
- Existing access JWTs issued before `auth_version` was required are rejected
  after deployment. Users must sign in again to obtain a versioned token.

## Redis availability

Configure `REDIS_URL` for the shared Redis service in development and
production. Native development uses `redis://localhost:6379/0`; containerized
deployments should use their Redis service hostname. Authenticated requests
must check the shared `jti` denylist, so they return HTTP 503 when Redis is
unavailable or unconfigured. Health and liveness endpoints remain independent
of Redis. The application does not use an in-memory fallback. Redis is created
once per application lifespan and closed during shutdown.
Use Redis 6.2 or newer because denylist entries use the `SET ... PXAT` absolute
expiration option.

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

Step 3.1 adds access-token version checks and Redis-backed individual token
revocation. Centralized RBAC, role/permission dependencies, business-resource
ownership/IDOR checks, general login and API rate limiting, security headers,
and broader security-event audit coverage remain later Step 3 work. Login and
email endpoints still require general rate limiting before production exposure.

See `API_CONTRACT_AUTH.md` for the frontend request and cookie contract.
