from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError

import app.services.opportunity_service as opportunity_service_module
from app.core.enums import OpportunityApplicationStatus, OpportunityStatus, OpportunityType, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.opportunity import OpportunityApplicationCreate, OpportunityApplicationReview, OpportunityCreate, OpportunityUpdate
from app.services.opportunity_service import OpportunityService


def _actor(role=UserRole.STUDENT):
    return SimpleNamespace(id=uuid4(), role=role)


def _opportunity(owner_id, status=OpportunityStatus.DRAFT, deadline=None):
    return SimpleNamespace(
        id=uuid4(), owner_id=owner_id, title="Opportunity", description="Description",
        organization="Alumni Co", opportunity_type=OpportunityType.JOB,
        location=None, application_url=None, deadline=deadline, status=status,
    )


def test_only_alumni_or_admin_can_create_opportunities():
    with pytest.raises(ForbiddenError):
        OpportunityService(Mock()).create(_actor(), OpportunityCreate(title="x", description="y", opportunity_type=OpportunityType.JOB, organization="z"))


def test_update_preserves_omitted_fields():
    actor = _actor(UserRole.ALUMNI)
    opportunity = _opportunity(actor.id)
    db = Mock()
    db.scalar.return_value = opportunity
    OpportunityService(db).update(actor, opportunity.id, OpportunityUpdate(title="Updated"))
    assert opportunity.title == "Updated"
    assert opportunity.description == "Description"
    assert opportunity.organization == "Alumni Co"


def test_publishing_expired_opportunity_is_rejected(monkeypatch):
    actor = _actor(UserRole.ALUMNI)
    opportunity = _opportunity(actor.id, deadline=datetime.now(UTC) - timedelta(minutes=1))
    db = Mock()
    db.scalar.return_value = opportunity
    monkeypatch.setattr(opportunity_service_module, "record_privileged_action", Mock())
    with pytest.raises(ConflictError, match="deadline must be in the future"):
        OpportunityService(db).publish(actor, opportunity.id)
    db.commit.assert_not_called()


def test_draft_opportunity_is_not_visible_to_other_users():
    actor = _actor()
    opportunity = _opportunity(_actor(UserRole.ALUMNI).id)
    db = Mock()
    db.get.return_value = opportunity
    with pytest.raises(NotFoundError):
        OpportunityService(db).get(actor, opportunity.id)


def test_owner_cannot_apply_to_own_opportunity():
    actor = _actor(UserRole.ALUMNI)
    opportunity = _opportunity(actor.id, OpportunityStatus.PUBLISHED)
    db = Mock()
    db.scalar.return_value = opportunity
    with pytest.raises(ForbiddenError):
        OpportunityService(db).apply(actor, opportunity.id, OpportunityApplicationCreate())


def test_withdrawn_application_can_be_reactivated(monkeypatch):
    actor = _actor()
    opportunity = _opportunity(_actor(UserRole.ALUMNI).id, OpportunityStatus.PUBLISHED)
    application = SimpleNamespace(status=OpportunityApplicationStatus.WITHDRAWN, cover_note="old", reviewed_at=datetime.now(UTC))
    db = Mock()
    db.scalar.side_effect = [opportunity, application]
    monkeypatch.setattr(opportunity_service_module, "record_privileged_action", Mock())
    result = OpportunityService(db).apply(actor, opportunity.id, OpportunityApplicationCreate(cover_note="new"))
    assert result is application
    assert application.status == OpportunityApplicationStatus.PENDING
    assert application.cover_note == "new"
    assert application.reviewed_at is None


def test_application_review_only_accepts_terminal_review_states():
    with pytest.raises(ValidationError):
        OpportunityApplicationReview(status=OpportunityApplicationStatus.PENDING)


def test_owner_can_accept_pending_application(monkeypatch):
    actor = _actor(UserRole.ALUMNI)
    opportunity = _opportunity(actor.id, OpportunityStatus.PUBLISHED)
    application = SimpleNamespace(id=uuid4(), opportunity_id=opportunity.id, applicant_id=uuid4(), status=OpportunityApplicationStatus.PENDING, reviewed_at=None)
    db = Mock()
    db.scalar.side_effect = [application, opportunity, application]
    monkeypatch.setattr(opportunity_service_module, "record_privileged_action", Mock())
    result = OpportunityService(db).review_application(actor, application.id, OpportunityApplicationReview(status=OpportunityApplicationStatus.ACCEPTED))
    assert result is application
    assert application.status == OpportunityApplicationStatus.ACCEPTED
    assert application.reviewed_at is not None


def test_opportunity_deadline_must_be_timezone_aware():
    with pytest.raises(ValidationError):
        OpportunityCreate(title="x", description="y", opportunity_type=OpportunityType.JOB, organization="z", deadline=datetime(2030, 1, 1))
