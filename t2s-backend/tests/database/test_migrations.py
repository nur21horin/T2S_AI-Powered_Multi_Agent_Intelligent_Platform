from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.pool import NullPool

from app.db.base import Base, NAMING_CONVENTION


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_configuration_uses_application_metadata_without_database_url():
    config = Config(str(BACKEND_ROOT / "alembic.ini"))

    assert Path(config.get_main_option("script_location")).resolve() == (
        BACKEND_ROOT / "alembic"
    ).resolve()
    assert config.get_main_option("sqlalchemy.url") == ""
    assert Base.metadata.naming_convention == NAMING_CONVENTION
    assert config.attributes.get("connection") is None


def test_model_package_imports_all_modules_for_metadata_registration():
    import app.models as models

    expected_modules = {
        "ai",
        "audit_log",
        "auth_token",
        "evaluation",
        "hackathon",
        "notification",
        "opportunity",
        "profile",
        "progress",
        "project",
        "research",
        "resource",
        "room",
        "skill",
        "submission",
        "task",
        "team",
        "user",
    }
    assert set(models.__all__) == expected_modules
    assert all(
        getattr(models, module).__name__ == f"app.models.{module}"
        for module in expected_modules
    )


def test_naming_convention_generates_stable_constraint_and_index_names():
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    Table("parent", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer),
        Column("code", String(20)),
        Column("amount", Integer),
        ForeignKeyConstraint(["parent_id"], ["parent.id"]),
        UniqueConstraint("code"),
        CheckConstraint("amount > 0", name="positive"),
    )
    Index(None, child.c.code)

    assert {constraint.name for constraint in child.constraints} == {
        "pk_child",
        "fk_child_parent_id_parent",
        "uq_child_code",
        "ck_child_positive",
    }
    assert {index.name for index in child.indexes} == {"ix_child_code"}


def test_autogenerate_upgrade_and_downgrade_on_isolated_test_schema(
    test_database_url: str, tmp_path: Path
):
    """Exercise real PostgreSQL migrations without leaving schema changes behind."""
    engine = create_engine(test_database_url, poolclass=NullPool)
    migrations_dir = tmp_path / "alembic"
    versions_dir = migrations_dir / "versions"
    versions_dir.mkdir(parents=True)
    shutil.copyfile(BACKEND_ROOT / "alembic" / "env.py", migrations_dir / "env.py")
    shutil.copyfile(
        BACKEND_ROOT / "alembic" / "script.py.mako", migrations_dir / "script.py.mako"
    )

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(migrations_dir).replace("%", "%%"))
    config.set_main_option("prepend_sys_path", str(BACKEND_ROOT).replace("%", "%%"))

    schema_name = f"alembic_test_{uuid.uuid4().hex}"
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema_name}"'))
                config.attributes["connection"] = connection

                command.revision(config, message="migration test", autogenerate=True)
                generated = list(versions_dir.glob("*.py"))
                assert len(generated) == 1

                command.upgrade(config, "head")
                upgraded_revision = MigrationContext.configure(connection).get_current_revision()
                assert upgraded_revision == generated[0].stem.split("_", maxsplit=1)[0]

                command.downgrade(config, "base")
                assert MigrationContext.configure(connection).get_current_revision() is None
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
