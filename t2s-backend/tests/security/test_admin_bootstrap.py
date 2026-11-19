from concurrent.futures import ThreadPoolExecutor
import io
import json
import logging
import sys
from threading import Barrier
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine

from app.core.config import Settings
from app.core.enums import UserRole
from app.core.exceptions import ConflictError
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.user_service import UserService
from scripts.create_admin import bootstrap_admin_interactively, main


def _settings(database_url: str, *, enabled: bool = True) -> Settings:
    return Settings(
        _env_file=None,
        app_env="testing",
        admin_bootstrap_enabled=enabled,
        database_url=SecretStr(database_url),
        db_pool_size=2,
        db_max_overflow=0,
    )


def test_bootstrap_requires_explicit_enablement_before_prompting(test_database_url):
    prompted = []

    with pytest.raises(RuntimeError, match="ADMIN_BOOTSTRAP_ENABLED"):
        bootstrap_admin_interactively(
            _settings(test_database_url, enabled=False),
            input_fn=lambda _prompt: prompted.append("input"),
            password_fn=lambda _prompt: prompted.append("password"),
        )

    assert prompted == []


def test_bootstrap_prompts_for_password_and_creates_first_admin_once(
    test_database_url, monkeypatch
):
    email = f"bootstrap-{uuid4().hex}@example.com"
    password = "bootstrap-test-password-123"
    prompts = []
    audit_events = []
    monkeypatch.setattr(
        "app.services.user_service.record_privileged_action",
        lambda **fields: audit_events.append(fields),
    )
    settings = _settings(test_database_url)
    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        admin_id = bootstrap_admin_interactively(
            settings,
            input_fn=lambda prompt: prompts.append(prompt)
            or (email if "email" in prompt else "First Admin"),
            password_fn=lambda prompt: prompts.append(prompt) or password,
        )
        assert prompts == [
            "Administrator email: ",
            "Administrator full name: ",
            "Administrator password: ",
            "Confirm administrator password: ",
        ]
        assert audit_events == [
            {
                "action": "admin.bootstrap.created",
                "actor_id": None,
                "target_id": admin_id,
            }
        ]

        with Session(engine) as db:
            admin = db.scalar(select(User).where(User.id == admin_id))
            assert admin.role == UserRole.ADMIN
            assert admin.is_active and admin.is_verified
            assert admin.password_hash != password
            original_hash = admin.password_hash

        with pytest.raises(ConflictError, match="already been completed"):
            with Session(engine) as db:
                UserService(db).bootstrap_initial_admin(
                    RegisterRequest(
                        email=email,
                        full_name="Changed",
                        password="another-valid-password-456",
                    )
                )
        with Session(engine) as db:
            admin = db.scalar(select(User).where(User.id == admin_id))
            assert admin.password_hash == original_hash
            assert admin.full_name == "First Admin"
    finally:
        with Session(engine) as db, db.begin():
            db.execute(delete(User).where(User.email == email))
        engine.dispose()


def test_bootstrap_refuses_to_promote_or_overwrite_existing_account(test_database_url):
    email = f"bootstrap-existing-{uuid4().hex}@example.com"
    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            existing = User(
                email=email,
                full_name="Existing Student",
                password_hash="existing-hash",
                role=UserRole.STUDENT,
                is_active=True,
                is_verified=True,
            )
            db.add(existing)
            db.commit()
            existing_id = existing.id
        with pytest.raises(ConflictError, match="account with this email"):
            with Session(engine) as db:
                UserService(db).bootstrap_initial_admin(
                    RegisterRequest(
                        email=email,
                        full_name="Overwrite",
                        password="valid-password-789",
                    )
                )
        with Session(engine) as db:
            existing = db.scalar(select(User).where(User.id == existing_id))
            assert existing.role == UserRole.STUDENT
            assert existing.full_name == "Existing Student"
            assert existing.password_hash == "existing-hash"
    finally:
        with Session(engine) as db, db.begin():
            db.execute(delete(User).where(User.email == email))
        engine.dispose()


def test_concurrent_bootstrap_creates_only_one_administrator(test_database_url):
    engine = create_engine(test_database_url, poolclass=NullPool)
    emails = [f"bootstrap-race-{uuid4().hex}@example.com" for _ in range(2)]
    barrier = Barrier(2)

    def bootstrap(index):
        with Session(engine) as db:
            barrier.wait(timeout=10)
            try:
                user = UserService(db).bootstrap_initial_admin(
                    RegisterRequest(
                        email=emails[index],
                        full_name="Bootstrap Race",
                        password="concurrent-bootstrap-password-456",
                    )
                )
                return ("created", user.email)
            except ConflictError:
                return ("refused", None)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(bootstrap, range(2), timeout=30))
        assert sorted(result[0] for result in results) == ["created", "refused"]
        with Session(engine) as db:
            admins = db.scalars(
                select(User).where(User.email.in_(emails), User.role == UserRole.ADMIN)
            ).all()
            assert len(admins) == 1
    finally:
        with Session(engine) as db, db.begin():
            db.execute(delete(User).where(User.email.in_(emails)))
        engine.dispose()


def test_cli_rejects_command_line_arguments_without_echoing_values(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["create_admin.py", "--password", "never-print-this"])

    assert main() == 2
    output = capsys.readouterr().out
    assert "never-print-this" not in output
    assert "--password" not in output


def test_actual_cli_emits_bootstrap_json_event_only_after_success(
    test_database_url, migrated_test_database, monkeypatch
):
    email = f"bootstrap-cli-audit-{uuid4().hex}@example.com"
    failed_email = f"bootstrap-cli-failed-{uuid4().hex}@example.com"
    password = "actual-cli-audit-password-123"

    class InteractiveTerminal:
        @staticmethod
        def isatty() -> bool:
            return True

    monkeypatch.setattr(sys, "argv", ["create_admin.py"])
    monkeypatch.setattr(sys, "stdin", InteractiveTerminal())
    monkeypatch.setattr(sys, "stderr", InteractiveTerminal())
    output_stream = io.StringIO()
    monkeypatch.setattr(sys, "stdout", output_stream)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", test_database_url)

    def invoke_cli(target_email):
        answers = iter([target_email, "CLI Audit Admin"])
        secrets = iter([password, password])
        return main(
            input_fn=lambda _prompt: next(answers),
            password_fn=lambda _prompt: next(secrets),
        )

    engine = create_engine(test_database_url, poolclass=NullPool)
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    uvicorn_access = logging.getLogger("uvicorn.access")
    original_uvicorn_access_disabled = uvicorn_access.disabled
    try:
        assert invoke_cli(email) == 0
        successful_output = output_stream.getvalue()
        events = [
            json.loads(line)
            for line in successful_output.splitlines()
            if line.startswith("{")
        ]
        bootstrap_events = [
            event for event in events if event.get("event") == "admin.bootstrap.created"
        ]
        assert len(bootstrap_events) == 1
        event = bootstrap_events[0]
        assert event["outcome"] == "success"
        assert event["actor_id"] is None
        assert event["target_id"]
        admin_id = event["target_id"]

        with Session(engine) as db:
            created = db.scalar(select(User).where(User.id == admin_id))
            assert created is not None
            assert created.email == email
            password_hash = created.password_hash
        assert email not in successful_output
        assert password not in successful_output
        assert password_hash not in successful_output

        output_stream.seek(0)
        output_stream.truncate(0)
        assert invoke_cli(failed_email) == 1
        failed_output = output_stream.getvalue()
        assert not any(
            json.loads(line).get("event") == "admin.bootstrap.created"
            for line in failed_output.splitlines()
            if line.startswith("{")
        )
        assert failed_email not in failed_output
        assert password not in failed_output
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
        uvicorn_access.disabled = original_uvicorn_access_disabled
        with Session(engine) as db, db.begin():
            db.execute(delete(User).where(User.email == email))
        engine.dispose()


def test_bootstrap_requires_database_configuration_before_prompting():
    prompted = []

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        bootstrap_admin_interactively(
            Settings(_env_file=None, app_env="testing", admin_bootstrap_enabled=True),
            input_fn=lambda _prompt: prompted.append("input"),
            password_fn=lambda _prompt: prompted.append("password"),
        )
    assert prompted == []


def test_bootstrap_password_confirmation_must_match(test_database_url):
    prompts = iter(
        [
            "bootstrap-mismatch@example.com",
            "Mismatch",
            "first-password-123",
            "second-password-456",
        ]
    )

    with pytest.raises(ValueError, match="do not match"):
        bootstrap_admin_interactively(
            _settings(test_database_url),
            input_fn=lambda _prompt: next(prompts),
            password_fn=lambda _prompt: next(prompts),
        )
