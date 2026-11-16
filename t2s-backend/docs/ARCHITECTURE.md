# Backend Architecture

## Database migrations

SQLAlchemy models inherit from `app.db.base.Base`. Its metadata defines stable
names for primary keys, foreign keys, unique constraints, check constraints,
and indexes. `app.models` imports model modules for Alembic metadata discovery;
model modules import `Base` from `app.db.base` and should use string-based ORM
relationship targets to avoid import cycles.

Alembic reads `DATABASE_URL` through the same Pydantic settings used by the
application. It does not create application tables at startup. Schema changes
are generated and applied explicitly with the commands in `docs/MIGRATIONS.md`.

## Access-token revocation

Access JWTs include the user's `auth_version`, which is checked against the
database on every authenticated request. Password changes and resets increment
that version in the same transaction as refresh-token revocation. Individual
logout revocation stores only the token `jti` in shared Redis until its expiry.
Redis is a required runtime dependency for authenticated routes and for logout
requests that revoke an access JWT; health endpoints do not depend on it.
