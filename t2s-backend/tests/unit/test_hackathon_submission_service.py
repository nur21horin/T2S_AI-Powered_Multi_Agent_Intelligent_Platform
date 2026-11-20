from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.enums import HackathonRegistrationStatus, HackathonSubmissionStatus, HackathonStatus, ProjectStatus, TeamStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError
from app.services.hackathon_submission_service import HackathonSubmissionService


def _hackathon(status=HackathonStatus.OPEN):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        organizer_id=uuid4(),
        status=status,
        registration_start_at=now - timedelta(days=1),
        start_at=now + timedelta(days=1),
    )


@pytest.mark.parametrize(
    ("current", "target"),
    (
        (HackathonSubmissionStatus.DRAFT, HackathonSubmissionStatus.SUBMITTED),
        (HackathonSubmissionStatus.DRAFT, HackathonSubmissionStatus.WITHDRAWN),
        (HackathonSubmissionStatus.SUBMITTED, HackathonSubmissionStatus.WITHDRAWN),
    ),
)
def test_submission_lifecycle_allows_only_defined_transitions(current, target):
    HackathonSubmissionService._assert_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    (
        (HackathonSubmissionStatus.SUBMITTED, HackathonSubmissionStatus.DRAFT),
        (HackathonSubmissionStatus.WITHDRAWN, HackathonSubmissionStatus.DRAFT),
        (HackathonSubmissionStatus.WITHDRAWN, HackathonSubmissionStatus.SUBMITTED),
    ),
)
def test_submission_lifecycle_rejects_skipped_or_terminal_transitions(current, target):
    with pytest.raises(ConflictError, match="Invalid hackathon submission lifecycle transition"):
        HackathonSubmissionService._assert_transition(current, target)


def test_submission_window_rejects_closed_or_future_deadlines():
    hackathon = _hackathon()
    HackathonSubmissionService._assert_submission_window(hackathon, datetime.now(UTC))

    with pytest.raises(ConflictError, match="not currently open"):
        HackathonSubmissionService._assert_submission_window(_hackathon(HackathonStatus.CLOSED), datetime.now(UTC))

    future = datetime.now(UTC) - timedelta(days=2)
    hackathon.registration_start_at = future
    hackathon.start_at = datetime.now(UTC) - timedelta(minutes=1)
    with pytest.raises(ConflictError, match="deadline has passed"):
        HackathonSubmissionService._assert_submission_window(hackathon, datetime.now(UTC))


def test_individual_submission_requires_project_owner_and_active_project():
    actor = SimpleNamespace(id=uuid4(), role=UserRole.STUDENT)
    service = HackathonSubmissionService(Mock())
    project = SimpleNamespace(owner_id=actor.id, team_id=None, status=ProjectStatus.ACTIVE)
    assert service._validate_project_access(actor, project) is None

    project.owner_id = uuid4()
    with pytest.raises(ForbiddenError, match="project owner"):
        service._validate_project_access(actor, project)

    project.owner_id = actor.id
    project.status = ProjectStatus.DRAFT
    with pytest.raises(ConflictError, match="Only active projects"):
        service._validate_project_access(actor, project)


def test_team_submission_requires_active_team_membership():
    actor = SimpleNamespace(id=uuid4())
    project = SimpleNamespace(owner_id=uuid4(), team_id=uuid4(), status=ProjectStatus.ACTIVE)
    db = Mock()
    db.scalar.side_effect = [SimpleNamespace(status=TeamStatus.ACTIVE), None]
    service = HackathonSubmissionService(db)

    with pytest.raises(ForbiddenError, match="active member"):
        service._validate_project_access(actor, project)


def test_team_registration_must_be_approved_and_include_submitter_snapshot():
    actor = SimpleNamespace(id=uuid4())
    registration = SimpleNamespace(id=uuid4(), status=HackathonRegistrationStatus.APPROVED)
    db = Mock()
    db.scalar.side_effect = [registration, object()]
    service = HackathonSubmissionService(db)

    assert service._approved_registration(actor, uuid4(), uuid4()) is registration
    assert db.scalar.call_count == 2
