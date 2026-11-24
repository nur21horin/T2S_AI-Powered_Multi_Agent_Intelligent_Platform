from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

import app.services.hackathon_service as hackathon_service_module
from app.core.enums import HackathonStatus, UserRole
from app.core.exceptions import BadRequestError
from app.schemas.hackathon import HackathonUpdate
from app.services.hackathon_service import HackathonService


def _service():
    actor = SimpleNamespace(id=uuid4(), role=UserRole.TEACHER)
    now = datetime.now(UTC)
    hackathon = SimpleNamespace(
        id=uuid4(),
        organizer_id=actor.id,
        status=HackathonStatus.DRAFT,
        title="Original title",
        slug="original-title",
        description="Original description",
        visibility="PUBLIC",
        participation_mode="BOTH",
        start_at=now + timedelta(days=2),
        end_at=now + timedelta(days=3),
        registration_start_at=now - timedelta(days=1),
        registration_end_at=now + timedelta(days=1),
        participant_limit=None,
        team_size_min=1,
        team_size_max=1,
        eligible_roles=[],
    )
    db = Mock()
    db.scalar.return_value = hackathon
    return HackathonService(db), actor, hackathon, db


@pytest.mark.parametrize("field", ("start_at", "end_at", "registration_start_at", "registration_end_at"))
def test_update_rejects_null_date_without_mutating_hackathon(monkeypatch, field):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon, db = _service()
    original = getattr(hackathon, field)

    with pytest.raises(BadRequestError, match="date fields cannot be null"):
        service.update(actor, hackathon.id, HackathonUpdate(**{field: None}))

    assert getattr(hackathon, field) == original
    db.commit.assert_not_called()


def test_update_omitted_dates_remain_unchanged(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon, db = _service()
    original_dates = tuple(getattr(hackathon, field) for field in ("start_at", "end_at", "registration_start_at", "registration_end_at"))

    service.update(actor, hackathon.id, HackathonUpdate(description="Updated description"))

    assert hackathon.description == "Updated description"
    assert tuple(getattr(hackathon, field) for field in ("start_at", "end_at", "registration_start_at", "registration_end_at")) == original_dates
    db.commit.assert_called_once()


def test_update_rejects_invalid_date_combination_before_mutation(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon, db = _service()
    original_end = hackathon.end_at

    with pytest.raises(BadRequestError, match="Hackathon dates or team-size bounds are invalid"):
        service.update(actor, hackathon.id, HackathonUpdate(end_at=hackathon.start_at - timedelta(minutes=1)))

    assert hackathon.end_at == original_end
    db.commit.assert_not_called()


def test_persisted_date_validation_rejects_null_override_without_type_error(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon, db = _service()

    with pytest.raises(BadRequestError, match="date fields cannot be null"):
        service._validate_persisted_dates(hackathon, {"start_at": None})

    db.commit.assert_not_called()


def test_update_rejects_null_non_nullable_team_size(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon, db = _service()

    with pytest.raises(BadRequestError, match="team_size_min cannot be null"):
        service.update(actor, hackathon.id, HackathonUpdate(team_size_min=None))

    assert hackathon.team_size_min == 1
    db.commit.assert_not_called()
