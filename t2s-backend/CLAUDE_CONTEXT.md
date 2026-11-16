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
sync vs async decided in Phase 1 and recorded here. No secrets in code; .env never committed.

## Rules for Claude
One feature at a time: Explain -> Implement (into existing files) -> Validate (really run tests) -> Report -> STOP.
Do not claim tests passed unless run. Do not push/commit; give git commands. Ask for branch name if unknown.
Update DEVELOPMENT_PROGRESS.md after each feature.

## Decisions log
- (Phase 0) Resource and ResearchOpportunity models included for task resources and AI search tools; no CRUD planned unless requested.
