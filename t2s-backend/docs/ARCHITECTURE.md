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
