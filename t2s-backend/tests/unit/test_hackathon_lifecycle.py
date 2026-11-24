from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

import app.services.hackathon_service as hackathon_service_module
from app.core.enums import HackathonStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.hackathon_service import HackathonService


def _service(status: HackathonStatus):
    actor = SimpleNamespace(id=uuid4(), role=UserRole.TEACHER)
    now = datetime.now(UTC)
    hackathon = SimpleNamespace(
        id=uuid4(),
        organizer_id=actor.id,
        status=status,
        registration_start_at=now - timedelta(minutes=1),
        registration_end_at=now + timedelta(minutes=1),
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=2),
        published_at=None,
        closed_at=None,
        completed_at=None,
        archived_at=None,
    )
    db = Mock()
    db.scalar.return_value = hackathon
    return HackathonService(db), actor, hackathon


def test_valid_hackathon_lifecycle_transitions(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon = _service(HackathonStatus.DRAFT)

    for target in (
        HackathonStatus.PUBLISHED,
        HackathonStatus.OPEN,
        HackathonStatus.CLOSED,
    ):
        service.transition(actor, hackathon.id, target)
        assert hackathon.status == target

    hackathon.end_at = datetime.now(UTC) - timedelta(seconds=1)
    service.transition(actor, hackathon.id, HackathonStatus.COMPLETED)
    service.transition(actor, hackathon.id, HackathonStatus.ARCHIVED)
    assert hackathon.status == HackathonStatus.ARCHIVED


@pytest.mark.parametrize(
    ("source", "target"),
    (
        (HackathonStatus.DRAFT, HackathonStatus.OPEN),
        (HackathonStatus.DRAFT, HackathonStatus.CLOSED),
        (HackathonStatus.PUBLISHED, HackathonStatus.CLOSED),
        (HackathonStatus.OPEN, HackathonStatus.COMPLETED),
        (HackathonStatus.CLOSED, HackathonStatus.ARCHIVED),
        (HackathonStatus.PUBLISHED, HackathonStatus.DRAFT),
        (HackathonStatus.OPEN, HackathonStatus.PUBLISHED),
        (HackathonStatus.CLOSED, HackathonStatus.OPEN),
        (HackathonStatus.COMPLETED, HackathonStatus.CLOSED),
    ),
)
def test_invalid_hackathon_lifecycle_transitions_are_rejected(monkeypatch, source, target):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon = _service(source)

    with pytest.raises(ConflictError, match="Invalid hackathon lifecycle transition"):
        service.transition(actor, hackathon.id, target)

    assert hackathon.status == source


def test_archived_hackathon_cannot_transition(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon = _service(HackathonStatus.ARCHIVED)

    with pytest.raises(NotFoundError, match="Hackathon not found"):
        service.transition(actor, hackathon.id, HackathonStatus.DRAFT)


def test_unauthorized_user_cannot_transition_hackathon(monkeypatch):
    monkeypatch.setattr(hackathon_service_module, "record_privileged_action", Mock())
    service, actor, hackathon = _service(HackathonStatus.DRAFT)
    unauthorized = SimpleNamespace(id=uuid4(), role=UserRole.STUDENT)

    with pytest.raises(ForbiddenError):
        service.transition(unauthorized, hackathon.id, HackathonStatus.PUBLISHED)
