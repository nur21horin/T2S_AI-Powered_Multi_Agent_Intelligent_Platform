from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import OpportunityApplicationStatus, OpportunityStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.opportunity import Opportunity, OpportunityApplication
from app.models.user import User
from app.schemas.opportunity import OpportunityApplicationCreate, OpportunityApplicationReview, OpportunityCreate, OpportunityUpdate
from app.services.audit_service import record_privileged_action
from app.utils.pagination import Pagination


class OpportunityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, data: OpportunityCreate) -> Opportunity:
        self._require_publisher(actor)
        values = data.model_dump()
        if values.get("application_url") is not None:
            values["application_url"] = str(values["application_url"])
        opportunity = Opportunity(owner_id=actor.id, **values)
        self.db.add(opportunity)
        self.db.commit()
        self.db.refresh(opportunity)
        record_privileged_action(action="opportunity_created", actor_id=actor.id, target_id=opportunity.id)
        return opportunity

    def list_public(self, actor: User, page: Pagination, opportunity_type=None) -> list[Opportunity]:
        query = select(Opportunity).where(Opportunity.status == OpportunityStatus.PUBLISHED)
        if opportunity_type is not None:
            query = query.where(Opportunity.opportunity_type == opportunity_type)
        return list(self.db.scalars(query.order_by(Opportunity.created_at.desc()).offset(page.offset).limit(page.limit)))

    def list_owned(self, actor: User, page: Pagination) -> list[Opportunity]:
        self._require_publisher(actor)
        query = select(Opportunity).where(Opportunity.owner_id == actor.id)
        return list(self.db.scalars(query.order_by(Opportunity.created_at.desc()).offset(page.offset).limit(page.limit)))

    def get(self, actor: User, opportunity_id: UUID) -> Opportunity:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if opportunity is None or (opportunity.status != OpportunityStatus.PUBLISHED and not self._can_manage(actor, opportunity)):
            raise NotFoundError("Opportunity not found.")
        return opportunity

    def update(self, actor: User, opportunity_id: UUID, data: OpportunityUpdate) -> Opportunity:
        opportunity = self._managed(actor, opportunity_id)
        if opportunity.status in {OpportunityStatus.CLOSED, OpportunityStatus.ARCHIVED}:
            raise ConflictError("Closed or archived opportunities cannot be edited.")
        values = data.model_dump(exclude_unset=True)
        if values.get("application_url") is not None:
            values["application_url"] = str(values["application_url"])
        for key, value in values.items():
            if isinstance(value, str) and key in {"title", "description", "organization", "location"}:
                value = value.strip()
            setattr(opportunity, key, value)
        self.db.commit()
        self.db.refresh(opportunity)
        record_privileged_action(action="opportunity_updated", actor_id=actor.id, target_id=opportunity.id)
        return opportunity

    def publish(self, actor: User, opportunity_id: UUID) -> Opportunity:
        opportunity = self._managed(actor, opportunity_id)
        if opportunity.status != OpportunityStatus.DRAFT:
            raise ConflictError("Only draft opportunities can be published.")
        if opportunity.deadline is not None and opportunity.deadline <= datetime.now(UTC):
            raise ConflictError("The opportunity deadline must be in the future.")
        opportunity.status = OpportunityStatus.PUBLISHED
        self.db.commit()
        self.db.refresh(opportunity)
        record_privileged_action(action="opportunity_published", actor_id=actor.id, target_id=opportunity.id)
        return opportunity

    def close(self, actor: User, opportunity_id: UUID) -> Opportunity:
        opportunity = self._managed(actor, opportunity_id)
        if opportunity.status != OpportunityStatus.PUBLISHED:
            raise ConflictError("Only published opportunities can be closed.")
        opportunity.status = OpportunityStatus.CLOSED
        self.db.commit()
        self.db.refresh(opportunity)
        record_privileged_action(action="opportunity_closed", actor_id=actor.id, target_id=opportunity.id)
        return opportunity

    def archive(self, actor: User, opportunity_id: UUID) -> None:
        opportunity = self._managed(actor, opportunity_id)
        if opportunity.status == OpportunityStatus.ARCHIVED:
            raise ConflictError("Opportunity is already archived.")
        opportunity.status = OpportunityStatus.ARCHIVED
        self.db.commit()
        record_privileged_action(action="opportunity_archived", actor_id=actor.id, target_id=opportunity.id)

    def apply(self, actor: User, opportunity_id: UUID, data: OpportunityApplicationCreate) -> OpportunityApplication:
        opportunity = self.db.scalar(select(Opportunity).where(Opportunity.id == opportunity_id).with_for_update())
        if opportunity is None or opportunity.status != OpportunityStatus.PUBLISHED:
            raise NotFoundError("Opportunity not found.")
        if opportunity.owner_id == actor.id:
            raise ForbiddenError("Opportunity owners cannot apply to their own opportunities.")
        if opportunity.deadline is not None and opportunity.deadline <= datetime.now(UTC):
            raise ConflictError("The opportunity application deadline has passed.")
        application = self.db.scalar(select(OpportunityApplication).where(OpportunityApplication.opportunity_id == opportunity_id, OpportunityApplication.applicant_id == actor.id).with_for_update())
        if application is not None and application.status != OpportunityApplicationStatus.WITHDRAWN:
            raise ConflictError("An application already exists for this opportunity.")
        if application is None:
            application = OpportunityApplication(opportunity_id=opportunity_id, applicant_id=actor.id, cover_note=data.cover_note)
            self.db.add(application)
        else:
            application.status = OpportunityApplicationStatus.PENDING
            application.cover_note = data.cover_note
            application.reviewed_at = None
        try:
            self.db.commit()
            self.db.refresh(application)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("An application already exists for this opportunity.") from None
        return application

    def list_my_applications(self, actor: User, page: Pagination) -> list[OpportunityApplication]:
        query = select(OpportunityApplication).where(OpportunityApplication.applicant_id == actor.id).order_by(OpportunityApplication.created_at.desc()).offset(page.offset).limit(page.limit)
        return list(self.db.scalars(query))

    def list_applications(self, actor: User, opportunity_id: UUID, page: Pagination) -> list[OpportunityApplication]:
        opportunity = self._managed(actor, opportunity_id)
        query = select(OpportunityApplication).where(OpportunityApplication.opportunity_id == opportunity.id).order_by(OpportunityApplication.created_at.desc()).offset(page.offset).limit(page.limit)
        return list(self.db.scalars(query))

    def review_application(self, actor: User, application_id: UUID, data: OpportunityApplicationReview) -> OpportunityApplication:
        application = self.db.scalar(select(OpportunityApplication).where(OpportunityApplication.id == application_id))
        if application is None:
            raise NotFoundError("Application not found.")
        self._managed(actor, application.opportunity_id)
        application = self.db.scalar(select(OpportunityApplication).where(OpportunityApplication.id == application_id).with_for_update())
        if application is None:
            raise NotFoundError("Application not found.")
        if application.status != OpportunityApplicationStatus.PENDING:
            raise ConflictError("Only pending applications can be reviewed.")
        application.status = data.status
        application.reviewed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(application)
        record_privileged_action(action="opportunity_application_reviewed", actor_id=actor.id, target_id=application.id)
        return application

    def withdraw_application(self, actor: User, application_id: UUID) -> OpportunityApplication:
        application = self.db.scalar(select(OpportunityApplication).where(OpportunityApplication.id == application_id).with_for_update())
        if application is None or application.applicant_id != actor.id:
            raise NotFoundError("Application not found.")
        if application.status != OpportunityApplicationStatus.PENDING:
            raise ConflictError("Only pending applications can be withdrawn.")
        application.status = OpportunityApplicationStatus.WITHDRAWN
        self.db.commit()
        self.db.refresh(application)
        return application

    @staticmethod
    def _require_publisher(actor: User) -> None:
        if actor.role not in {UserRole.ALUMNI, UserRole.ADMIN}:
            raise ForbiddenError("Only alumni or administrators can manage opportunities.")

    @staticmethod
    def _can_manage(actor: User, opportunity: Opportunity) -> bool:
        return actor.role == UserRole.ADMIN or actor.id == opportunity.owner_id

    def _managed(self, actor: User, opportunity_id: UUID) -> Opportunity:
        opportunity = self.db.scalar(select(Opportunity).where(Opportunity.id == opportunity_id).with_for_update())
        if opportunity is None:
            raise NotFoundError("Opportunity not found.")
        if not self._can_manage(actor, opportunity):
            raise ForbiddenError()
        return opportunity
