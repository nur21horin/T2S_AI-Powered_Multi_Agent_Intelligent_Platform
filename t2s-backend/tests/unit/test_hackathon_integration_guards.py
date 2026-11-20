from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

import app.services.hackathon_service as hackathon_service_module
import app.services.project_service as project_service_module
import app.services.team_service as team_service_module
from app.core.enums import HackathonRegistrationStatus, HackathonRegistrationType, HackathonStatus, ProjectStatus, UserRole
from app.core.exceptions import ConflictError
from app.services.hackathon_service import HackathonService
from app.services.project_service import ProjectService
from app.services.team_service import TeamService
from app.core.enums import TeamStatus


def test_project_archive_is_rejected_when_it_has_a_hackathon_submission(monkeypatch):
    actor = SimpleNamespace(id=uuid4(), role=UserRole.STUDENT)
    project = SimpleNamespace(id=uuid4(), owner_id=actor.id, status=ProjectStatus.ACTIVE)
    db = Mock()
    db.scalar.side_effect = [project, uuid4()]
    monkeypatch.setattr(project_service_module, "record_privileged_action", Mock())

    with pytest.raises(ConflictError, match="cannot be archived"):
        ProjectService(db).archive(actor, project.id)

    db.commit.assert_not_called()


def test_project_team_change_is_rejected_when_it_has_a_hackathon_submission(monkeypatch):
    actor = SimpleNamespace(id=uuid4(), role=UserRole.STUDENT)
    project = SimpleNamespace(id=uuid4(), owner_id=actor.id, status=ProjectStatus.ACTIVE, team_id=uuid4())
    db = Mock()
    db.scalar.side_effect = [project, uuid4()]
    monkeypatch.setattr(project_service_module, "record_privileged_action", Mock())

    with pytest.raises(ConflictError, match="cannot change team association"):
        ProjectService(db).attach_team(actor, project.id, uuid4())

    db.commit.assert_not_called()


def test_team_archive_is_rejected_when_it_has_a_hackathon_submission(monkeypatch):
    actor = SimpleNamespace(id=uuid4(), role=UserRole.STUDENT)
    team = SimpleNamespace(id=uuid4(), owner_id=actor.id, status=TeamStatus.ACTIVE)
    db = Mock()
    db.scalar.side_effect = [team, uuid4()]
    monkeypatch.setattr(team_service_module, "record_privileged_action", Mock())

    with pytest.raises(ConflictError, match="cannot be archived"):
        TeamService(db).archive(actor, team.id)

    db.commit.assert_not_called()


def test_approved_registration_with_submission_cannot_be_cancelled():
    registration = SimpleNamespace(
        hackathon_id=uuid4(),
        registration_type=HackathonRegistrationType.INDIVIDUAL,
        participant_id=uuid4(),
        team_id=None,
        status=HackathonRegistrationStatus.APPROVED,
    )
    db = Mock()
    db.scalar.return_value = uuid4()

    assert HackathonService(db)._has_submission(registration) is True


def test_registration_review_is_rejected_after_hackathon_leaves_open():
    actor = SimpleNamespace(id=uuid4(), role=UserRole.TEACHER)
    registration = SimpleNamespace(status=HackathonRegistrationStatus.PENDING, hackathon_id=uuid4())
    hackathon = SimpleNamespace(status=HackathonStatus.CLOSED, organizer_id=actor.id)
    db = Mock()
    db.scalar.side_effect = [registration, hackathon]

    with pytest.raises(ConflictError, match="while the hackathon is open"):
        HackathonService(db).review(actor, uuid4(), True)

    db.commit.assert_not_called()
