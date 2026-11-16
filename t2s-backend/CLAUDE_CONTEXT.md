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
