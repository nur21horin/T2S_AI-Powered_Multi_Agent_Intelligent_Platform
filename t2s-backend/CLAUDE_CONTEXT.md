# CLAUDE_CONTEXT.md — resume guide (give this + DEVELOPMENT_PROGRESS.md to a new chat)

## Project
T2S: AI-powered multi-agent platform (students / teachers / alumni / admin). I am **Team Member 2: backend + DB only**.
No frontend, no AI agents (Member 3). Proposal PDF is the source of truth.

## Stack (do not add more without explaining)
Python, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2.x, Alembic, PostgreSQL (+pgvector-ready),
JWT + refresh tokens, Argon2id, Redis (shared rate limiting/denylist), Nginx (load balancer), Docker Compose, Pytest + HTTPX.

## Architecture (layers; dependencies point downward only)
api/v1/endpoints -> services -> repositories -> models (db)
Cross-cutting: core (config, logging, exceptions), security (passwords, tokens, cookies, csrf, permissions, ownership, rate_limit, service_auth), middleware, schemas, tasks, utils.
- Endpoints: thin; validate via schemas, call services. Never return ORM models directly.
- Authorization: centralized in security/permissions.py (role) + security/ownership.py (object-level). Backend is the authority.
- AI module access only through /api/v1/ai-tools/* authenticated with service key; no raw DB access; data-minimized responses.
- Migrations via Alembic only; never create_all in production.
- API prefix /api/v1; consistent response/error envelope in schemas/common.py.

## Conventions
PEP8, type hints, UUID primary keys, timestamps (created_at/updated_at, UTC), soft-delete only where justified,
**Sync** SQLAlchemy (psycopg3) with plain `def` endpoints (decided Phase 1: simpler, safe with CPU-bound Argon2). No secrets in code; .env never committed.

## Rules for Claude
One feature at a time: Explain -> Implement (into existing files) -> Validate (really run tests) -> Report -> STOP.
Do not claim tests passed unless run. Do not push/commit; give git commands. Ask for branch name if unknown.
Update DEVELOPMENT_PROGRESS.md after each feature.

## Decisions log
- (Phase 0) Resource and ResearchOpportunity models included for task resources and AI search tools; no CRUD planned unless requested.
- (Phase 1) Success responses return the resource directly (no envelope). Errors: {"error": {code, message, details, request_id}}.
- (Phase 1) Validation errors strip submitted input (no secret echo). Docs/OpenAPI disabled when APP_ENV=production.
- (Phase 1) Middleware order (outer->inner): RequestID > AccessLog > TrustedHost > CORS. Security headers come in Phase 3.
- (Phase 1) requirements pin top-level deps only, added per feature. uvicorn without [standard] for now (Windows-safe); revisit in Phase 14.
- App factory: app.main.create_app(settings). Tests build Settings(_env_file=None, ...).
- (1.2) DB: engine created lazily in lifespan (app.state.engine / session_factory); app starts even if DB is down. get_db(request) in api/deps.py = one Session per request, services commit explicitly, rollback on error, always closed. pool_pre_ping, connect_timeout 5s, statement_timeout 30s. DATABASE_URL is SecretStr.
- (1.2) /health = liveness (no DB). /health/ready = readiness (SELECT 1, 503 if DB down) -> used by Nginx/LB later.
- (1.2) Dev DB: native PostgreSQL 16 on Windows (no Docker until Phase 14). Databases: t2s (dev), t2s_test (tests). Tests need TEST_DATABASE_URL (env or .env); DB name must end with _test or tests fail; DB tests skip if unset.
- (Step 2) Public registration always assigns STUDENT; client role fields are ignored. Unverified or inactive users cannot log in, refresh, or use authenticated routes. Teacher/alumni/admin provisioning and RBAC are deferred to Step 3.
- (Step 2) Passwords use Argon2id. Access JWTs use fixed HS256, issuer/audience validation, and a 15-minute default lifetime. Production requires JWT_SECRET_KEY of at least 32 bytes. Refresh tokens are opaque, random, stored only as SHA-256 hashes, rotated atomically, and grouped into revocable families; reuse revokes the family.
- (Step 2) Refresh uses an HttpOnly cookie; access JWT is returned in the response and used as a Bearer token. CSRF uses a signed double-submit cookie/header plus exact Origin validation for refresh/logout; login validates Origin. The CSRF endpoint supports browser reload. Frontend must keep access tokens in memory, never localStorage.
- (Step 2) Email verification, verification resend, password reset, and password change are implemented. Email delivery uses an injectable sender; tests use a fake. SMTP may use STARTTLS or implicit SSL. Email-dependent flows fail with 503 when delivery is not configured. Recovery responses are generic.
- (Step 2) Auth tables: users and auth_tokens. Migration: `alembic/versions/d713be9dc4b9_add_authentication_tables.py`. Dedicated `_test` DB is upgraded to head by integration-test setup; migration tests also apply and downgrade the committed revision in a transaction-scoped temporary schema.
- (Step 3.1) Users have `auth_version`; access JWTs include it and `get_current_user` compares it with the database. Password change/reset increments it and revokes refresh tokens in the same transaction. No role-change operation exists yet; any future authorized operation must increment the version in its transaction.
- (Step 3.1) Logout still revokes the refresh family and accepts an optional Bearer access token for Redis `jti` revocation. Redis outages fail closed with HTTP 503 for authenticated requests and access-token revocation; no in-memory fallback exists. `REDIS_URL` is required for protected routes.
- (Step 3.1) Existing access JWTs without `auth_version` are rejected after deployment; users must sign in again. General rate limiting, RBAC, ownership/IDOR helpers, and security headers remain later Step 3 work.
