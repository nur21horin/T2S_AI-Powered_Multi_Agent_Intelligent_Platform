# DEVELOPMENT_PROGRESS.md

**Current development step:** Master Step 4 — Profile & Technical Room Management (implemented; Steps 5–8 pending)
**Completed:** Phase 0 structure; 1.1 app skeleton, settings, JSON logging, request ID, access log, CORS, TrustedHost, centralized errors, and GET /api/v1/health; 1.2 SQLAlchemy engine/session, get_db, and GET /api/v1/health/ready (21 tests previously reported passing against PostgreSQL 16); 1.3 declarative base, metadata naming conventions, Alembic configuration/model discovery, and migration verification; Step 2 student registration, email verification, Argon2id password handling, login/logout, signed access JWT, opaque refresh-token rotation/revocation/reuse detection, current-user endpoint, password recovery/change, SMTP boundary, and refresh-cookie CSRF/origin protection; Step 3.1 database-backed access-token versioning, password-change/reset invalidation, Redis `jti` denylist, and idempotent Redis-before-PostgreSQL logout.
**Step 3.1 verification:** Full backend suite: 62 passed, 1 non-failing Starlette/httpx deprecation warning. Migration tests upgraded and downgraded the new revision in an isolated PostgreSQL schema, verified an existing user survived with `auth_version=0`, and confirmed downgrade removed only the new column. Redis failure behavior and client lifecycle passed fake-client tests; no local Redis server or Docker was available for live-server integration.
**Step 2 verification:** Full backend suite: 47 passed, 2 non-failing environment warnings. Migration tests generated a revision, and applied/downgraded both generated and committed auth migrations in isolated PostgreSQL schemas within transactions.
**Pending in Step 2:** none.
**Files modified (1.1):** app/main.py, core/{config,logging,exceptions,lifespan}.py, schemas/common.py, middleware/{request_id,access_log}.py, api/v1/{router.py,endpoints/health.py}, requirements*.txt, pyproject.toml, .env.example, tests/{conftest.py,unit/test_config.py,api/test_health.py,security/test_input_validation.py}
**Files modified (1.2):** requirements.txt, .env.example, core/{config,exceptions,lifespan}.py, main.py, schemas/common.py, api/deps.py, api/v1/endpoints/health.py, db/session.py, tests/{conftest.py,unit/test_config.py,database/test_connection.py}
**Step 2 files:** requirements.txt, .env.example, app/core/{config,enums}.py, app/db/mixins.py, app/models/{__init__,user,auth_token}.py, app/schemas/{auth,user}.py, app/security/{passwords,tokens,cookies,csrf}.py, app/repositories/{user_repository,token_repository}.py, app/services/{auth_service,email_service}.py, app/api/{deps.py,v1/router.py,v1/endpoints/auth.py}, app/main.py, alembic/versions/d713be9dc4b9_add_authentication_tables.py, tests/{conftest.py,factories.py,unit/test_config.py,unit/test_passwords.py,unit/test_tokens.py,api/test_auth.py,security/test_authentication_security.py,security/test_input_validation.py,database/test_migrations.py}, docs/{SECURITY.md,API_CONTRACT_AUTH.md}, CLAUDE_CONTEXT.md.
**Migrations:** `users` and `auth_tokens` are in the new application migration. The dedicated `TEST_DATABASE_URL` database is upgraded to head by the integration-test setup. The migration's upgrade and downgrade were also verified in a temporary schema inside a rolled-back transaction.
**Step 3.1 files:** requirements.txt, .env.example, app/{api/deps.py,api/v1/endpoints/auth.py,core/config.py,core/lifespan.py,main.py,models/user.py,repositories/user_repository.py,security/tokens.py,security/revocation.py,services/auth_service.py}, alembic/versions/8a6c2f17d4b0_add_user_auth_version.py, tests/{api/test_auth.py,api/test_logout_reliability.py,api/test_health.py,database/test_migrations.py,security/test_token_revocation.py,unit/test_redis_lifecycle.py,unit/test_tokens.py,conftest.py}, docs/{ARCHITECTURE.md,API_CONTRACT_AUTH.md,SECURITY.md}, CLAUDE_CONTEXT.md, DEVELOPMENT_PROGRESS.md.
**Issues (historical Step 3.1):** Real Redis-server integration was unavailable in the Step 3.1 environment; that verification used a fake Redis client. The Starlette TestClient/httpx deprecation warning remains non-failing.
**Next task:** Review Step 3 implementation; run the documented live-Redis suite when a dedicated Redis 6.2+ test service is provisioned. No Master Step 4 work is included.

## Master Step 3 audit and implementation status (2026-11-19)

The mounted backend scope remains authentication/health plus administrator role management; placeholder domain APIs were not implemented because those belong to later roadmap steps. No dependency or migration was added.

| Step 3 item | Implementation status | Verification status |
|---|---|---|
| 3.1 access-token versioning/revocation | Previously complete | Existing regression suite remains green |
| 3.2.1 Redis rate-limit foundation | Previously complete | Unit/config tests pass |
| 3.2.2 authentication rate limits and HMAC identifiers | Previously complete | Endpoint, policy, config, normalization, and Retry-After tests pass |
| 3.2.3.1 isolated real-Redis test fixture | Complete | Safety/cleanup tests pass; live connection skipped because test Redis opt-in is absent |
| 3.2.3.2 single-key Lua and TTL integration tests | Implemented; live verification pending | Six tests are present; not executed against a live Redis service in this environment |
| 3.2.3.3 multi-key Lua integration tests | Implemented; live verification pending | Preflight, counters, limits, TTL repair/preservation, and wrong-type no-write coverage present; live execution skipped |
| 3.2.3.4 concurrency/cross-worker verification | Implemented; live Redis verification pending | Shared real-Redis cases skipped; PostgreSQL concurrent role/bootstrap lock tests passed |
| 3.2.3.5 Redis failure and HTTP 503 | Complete | Deterministic HTTP tests cover connection, timeout, script, malformed response, safe message, and fail-closed behavior |
| 3.2.3.6 endpoint policy regression | Complete | Authentication rate-limit and failed-login behavior tests pass |
| 3.2.3.7 HMAC/configuration/Retry-After | Complete | Configuration, digest, identifier, policy and response-header tests pass |
| 3.2.3.8 CSRF/Origin/CORS/logout | Complete | Route-specific Origin/CSRF order, logout reliability, CORS and no-rate-limit behavior tests pass |
| 3.2.3.9 security documentation | Complete | Security, setup, environment, bootstrap, and progress docs updated |
| 3.2.3.10 backend verification | Complete with live-Redis limitation | Full suite: 157 passed, 16 real-Redis integration tests skipped, 1 non-failing Starlette/httpx deprecation warning |
| 3.3 default-deny RBAC/ownership | Complete for mounted API scope | Role allow/deny, unauthenticated access, ownership checks, self-role denial and role-change token invalidation pass |
| Admin bootstrap and final-admin protection | Complete | Interactive one-time bootstrap and concurrent PostgreSQL serialization tests pass; no deactivation/deletion API exists |
| Structured audit events/security headers | Complete | Role/bootstrap event structure and response headers (including unhandled 500 and CORS preflight) pass |

### Step 3 verification details

The backend full-suite command was `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -rs`: **157 passed, 16 skipped, 0 failed**. All 16 skips are the real-Redis integration tests because neither `TEST_REDIS_URL` nor explicit `TEST_REDIS_INTEGRATION=1` is configured. They were not redirected to `REDIS_URL`, and no Redis service was contacted. The standalone administrator bootstrap CLI now explicitly re-enables and routes its privileged audit logger through the configured JSON root handler; the actual CLI test verifies one success event and no false event after failure. To complete live-server verification, provision an isolated Redis 6.2+ test service and set those two test-only variables as described in `docs/SECURITY.md`.

No migration was necessary: roles and `auth_version` already exist in the user schema; privileged audit events use the existing structured application logger. PostgreSQL integration verification used PostgreSQL 16.16. Ruff and mypy executables are not present in the checked-in virtual environment, so no optional lint/type checker was run. `git diff --check` passed.

## Master Step 4 — Profile & Technical Room Management (2026-11-19)

Implemented explicit one-to-one student, teacher, and alumni profiles;
normalized shared skills and interests; technical rooms with public/private
visibility; owner memberships; and transactional membership requests with
PENDING, APPROVED, REJECTED, and CANCELLED states. Profile and room ownership
are always derived from the authenticated user. Shared catalog deletion and
room ownership transfer are intentionally not exposed.

The new migration is `c4e7a1b2d903_add_profiles_skills_and_rooms.py`. The final
Step 4 audit fixed room-bound request cancellation, membership reactivation
after leave, archived-room decisions, nullable room update handling, and
concurrent catalog creation rollback behavior. Full backend verification:
**167 passed, 16 skipped, 0 failed**, with the existing Starlette/httpx
deprecation and pytest cache-permission warnings. The 16 skips are opt-in
real-Redis integration tests; no dedicated Redis service was available.
PostgreSQL migration and API tests used PostgreSQL 16.16. Ruff and mypy are not
installed in the checked-in virtual environment; `git diff --check` passed.

## Roadmap
1 Foundation | 2 Authentication | 3 Authorization & Security | 4 Profiles | 5 Rooms | 6 Tasks |
7 Submissions & Evaluation | 8 Progress & Skills | 9 Projects & Teams | 10 Hackathons |
11 Alumni Opportunities | 12 Notifications | 13 AI Integration Interfaces | 14 Load Balancing & Deployment | 15 Final Testing & Docs

**Eight-phase roadmap mapping:** 15-step Step 2 implements the authentication portion of original Phase 3. Step 3.1 adds access-token revocation/versioning; later Step 3 substeps cover centralized authorization and broader application-security requirements.
