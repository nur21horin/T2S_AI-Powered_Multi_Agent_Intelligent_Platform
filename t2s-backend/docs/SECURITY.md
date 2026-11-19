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
  previously issued access JWTs. The ADMIN-only role-assignment operation
  updates the role and increments `auth_version` in one database transaction.
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

## Rate limiting

Rate limits use the application-managed shared Redis client configured by
`REDIS_URL`; there is no in-memory fallback. Protected rate-limited endpoints
fail closed with HTTP 503 if Redis is missing, unavailable, times out, returns
a script error, or returns a malformed script result. Rejected requests receive
HTTP 429 with a `Retry-After` header. Email/IP/user identifiers are normalized,
domain-separated and HMAC-SHA256 digested with the independently configured
`RATE_LIMIT_KEY_SECRET` (minimum 32 bytes); raw identifiers are not put in Redis
keys. Production requires this secret. Do not reuse the JWT signing secret.

Current endpoint policies are:

| Operation | Dimension | Limit |
|---|---|---:|
| Login | Direct client IP | 10 / 15 minutes |
| Failed login credentials | Normalized account email | 5 / 15 minutes |
| Registration | Direct client IP | 5 / hour |
| Email verification | Direct client IP | 10 / hour |
| Verification resend | Email and direct client IP | 3 / hour; 10 / hour |
| Forgot password | Email and direct client IP | 3 / hour; 10 / hour |
| Password reset | Direct client IP | 5 / hour |
| Refresh | Direct client IP | 30 / minute |
| Password change | Authenticated user UUID | 5 / 15 minutes |

Multi-key operations preflight all policy and key state before normal counter
writes, so invalid TTL and wrong-type state do not consume another dimension.
Redis Lua does not roll back earlier writes after arbitrary later runtime or
out-of-memory errors; no rollback guarantee is made for those failures.

Only the ASGI peer address is used. Forwarded IP headers are ignored unless a
future explicit trusted-proxy design is implemented. `/csrf`, `/me`, and
logout have no rate-limit bucket. Successful login does not spend the failed
account bucket; the IP login bucket applies to all login attempts.

Real Redis tests are opt-in and require an isolated Redis service: configure
`TEST_REDIS_URL` and explicitly set `TEST_REDIS_INTEGRATION=1`. Never point it
to application `REDIS_URL`, production Redis, or shared development Redis.
The pytest fixture reads both test variables from the process environment;
putting them only in the backend `.env` file does not enable these tests.
Tests use unique test-owned keys and delete only explicitly registered keys;
they never flush a database or scan/delete by pattern. If `TEST_REDIS_URL` is
absent, only tests requiring real Redis are skipped. A configured but unsafe or
unreachable target fails tests. The minimum remains Redis 6.2+.

## Cookie and CSRF protections

- Refresh tokens use an HttpOnly cookie. `Secure` is forced in production and
  when `SameSite=None` is selected. SameSite, cookie name, domain, and path are
  configurable. The default path is `/api/v1/auth`.
- A separate signed CSRF cookie is paired with the `X-CSRF-Token` request
  header. Refresh and logout each require a valid pair and an exact `Origin`
  match in `CORS_ALLOWED_ORIGINS`; refresh validates these before its rate
  limit. Logout is not rate-limited. SameSite is an additional browser control,
  not the only CSRF defense.
- Login checks that the request has an allowed Origin because it establishes
  the refresh cookie, but it does not require CSRF. `GET /api/v1/auth/csrf`
  checks allowed Origin and the current valid refresh/CSRF cookie pair; it does
  not require the CSRF header to return the token. Browser clients use
  credentials for refresh/logout and send the CSRF token returned by
  login/refresh. After a page reload, obtain the current token from the CSRF
  endpoint.
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

## Authorization and administrator operations

Authorization is default-deny. The existing STUDENT, TEACHER, ALUMNI, and
ADMIN roles receive no implicit broad access. Only explicitly mapped
permissions are granted; currently ADMIN has `admin.users.manage_roles`.
Student/teacher/alumni access to future private resources must combine explicit
role permission and an independent ownership check. ADMIN status does not
silently bypass ownership. No unapproved domain CRUD endpoints are introduced.

| Role | Explicit permissions currently implemented |
|---|---|
| STUDENT | None in the mounted API beyond authenticated self-service routes |
| TEACHER | None in the mounted API |
| ALUMNI | None in the mounted API |
| ADMIN | `admin.users.manage_roles` |

`PATCH /api/v1/admin/users/{user_id}/role` requires an authenticated active,
verified ADMIN. An administrator cannot change their own role. A role update
and `auth_version` increment commit atomically, invalidating old access tokens.
Role changes are serialized using a PostgreSQL transaction advisory lock and
emit structured events with actor/target IDs and old/new roles, never
credentials. Bootstrap uses the same lock. The final active administrator
cannot be demoted by concurrent role changes. Future deactivate/delete paths
must use the same lock and guard; none currently exist.

Bootstrap the first ADMIN by setting `ADMIN_BOOTSTRAP_ENABLED=true` and running
`python -m scripts.create_admin` from the backend directory. The CLI prompts
for email/name and twice for the password using hidden terminal input; it never
accepts credentials as command-line arguments. It refuses if any ADMIN or the
requested email already exists and never overwrites or promotes an account.
Set `ADMIN_BOOTSTRAP_ENABLED=false` immediately after success. If the only
administrator becomes inaccessible, the CLI cannot create a replacement.
Recovery requires a maintenance-window database operator to restore an
existing trusted account's ADMIN role and active status in one transaction,
acquire the same PostgreSQL advisory transaction lock used by
`UserRepository.lock_admin_state()`, increment `auth_version`, and record the
intervention in the protected operational audit trail; then use normal
password recovery. There is no public recovery endpoint or credential reset
shortcut.

## Audit events and response headers

Privileged role assignments and initial administrator creation emit structured
JSON audit events with event name, outcome, request ID when available, and safe
actor/target identifiers and role values. Passwords, tokens, CSRF values, HMAC
secrets, and request bodies are excluded. The existing access logger records
method, path, status, duration, and request ID without query strings or request
bodies, so authentication/authorization response statuses remain observable
without logging credentials or submitted identifiers. There is no audit
database table or migration. Responses receive `X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`, and `Permissions-Policy`, including errors and CORS
preflights. The audit events use the application's JSON logger; deployment
log collection and retention must route these events to a protected central
sink. CORS accepts only configured origins; `Retry-After` is exposed.

Run focused authorization and bootstrap checks from `t2s-backend/`:

```powershell
python -m pytest -q tests/unit/test_permissions.py tests/security/test_authorization_idor.py tests/security/test_admin_bootstrap.py tests/api/test_admin.py
```

For real Redis integration, start or provision a dedicated isolated Redis
service (for example, a test-only instance on `127.0.0.1:6389`, with no shared
application data). In PowerShell, set only the test target and explicit opt-in:

```powershell
$env:TEST_REDIS_URL = "redis://127.0.0.1:6389/0"
$env:TEST_REDIS_INTEGRATION = "1"
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_rate_limit_redis.py tests/integration/test_multi_rate_limit_redis.py tests/integration/test_rate_limit_concurrency.py
```

Do not set `TEST_REDIS_URL` to a production, shared development, or application
Redis endpoint. Run the full backend suite with `.\.venv\Scripts\python.exe -m pytest -q`.

See `API_CONTRACT_AUTH.md` for the frontend request and cookie contract.

## Profile and technical room authorization

Profile writes are limited to the authenticated user's role-specific profile;
role, account identity, and verification fields are not accepted as profile
input. Skills and interests are normalized and associated through unique join
constraints; users cannot delete shared catalog records.

Room owners are assigned from the authenticated principal. Public visibility is
only discoverability and never implies membership. Private rooms, member lists,
and pending requests require the owner or an active member as appropriate.
Only owners can update/archive rooms or approve/reject membership requests.
Request state transitions are validated server-side, pending requests are
unique per user and room, and approval creates membership and updates request
state in one transaction. Owner membership cannot be removed through the leave
operation, and ownership transfer is not implemented.

## Task and submission authorization

Tasks are scoped to technical rooms. Room owners and active teacher members may
create, edit, publish, close, or archive tasks. Draft tasks are hidden from
ordinary room viewers. Public rooms may expose published task information, but
submission creation requires an active room membership; private room and
archived-room access is enforced server-side.

Submission ownership, attempt numbers, status, and timestamps are assigned or
validated by the service layer. Students may submit only to published tasks
within the schedule and may resubmit only when the task policy and attempt limit
allow it. Evaluations are limited to room owners and active teacher members;
self-evaluation, cross-user access, score-over-maximum, and client-controlled
evaluator identity are rejected. Progress is calculated from database records
and cannot be directly modified by clients.
## Step 6 Phase 1 collaboration controls

Project and team authorization is enforced in services rather than trusting client-supplied owner identifiers. Team owners and active delegated leaders manage team metadata, invitations, and join-request decisions; ordinary members cannot perform those actions. Owners cannot leave their own teams, and a leader cannot replace or transfer ownership. Join-request and invitation approval are row-locked and membership uniqueness is enforced by PostgreSQL partial indexes to prevent duplicate active memberships under concurrency.

Public resources are discoverable but do not grant membership. Private project details require the owner or active team membership; private team details and member lists require active membership. Project association requires project ownership plus active membership in the selected team. Audit events contain bounded action names and UUIDs only; credentials, tokens, invitation contents, and request bodies are not logged.
