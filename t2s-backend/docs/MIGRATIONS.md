# Database migrations

Alembic is the only supported mechanism for changing the database schema.
Application startup does not create tables. Run commands from `t2s-backend/`
with the project virtual environment active and `DATABASE_URL` set in the
environment or `.env`.

Generate a revision from model metadata:

```powershell
alembic revision --autogenerate -m "describe schema change"
```

Review and edit every generated revision before applying it. Autogeneration is
a proposal, not a substitute for reviewing data migrations or database-specific
operations.

Apply all revisions:

```powershell
alembic upgrade head
```

Roll back one revision or all revisions:

```powershell
alembic downgrade -1
alembic downgrade base
```

Inspect the current database revision and available history:

```powershell
alembic current
alembic history
```

For tests, set `TEST_DATABASE_URL` to a dedicated PostgreSQL database whose
name ends in `_test`. Migration integration tests create a temporary schema
inside a transaction and roll it back, leaving the test database unchanged.
