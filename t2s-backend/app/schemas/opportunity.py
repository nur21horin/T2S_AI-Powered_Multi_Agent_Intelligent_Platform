from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.core.enums import OpportunityApplicationStatus, OpportunityStatus, OpportunityType


class OpportunityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=10000)
    opportunity_type: OpportunityType
    organization: str = Field(min_length=1, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    application_url: HttpUrl | None = None
    deadline: datetime | None = None

    @model_validator(mode="after")
    def validate_datetime(self):
        if self.deadline is not None and self.deadline.tzinfo is None:
            raise ValueError("deadline must include a timezone.")
        return self


class OpportunityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    opportunity_type: OpportunityType | None = None
    organization: str | None = Field(default=None, min_length=1, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    application_url: HttpUrl | None = None
    deadline: datetime | None = None

    @model_validator(mode="after")
    def validate_datetime(self):
        if self.deadline is not None and self.deadline.tzinfo is None:
            raise ValueError("deadline must include a timezone.")
        return self


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    title: str
    description: str
    opportunity_type: OpportunityType
    organization: str
    location: str | None
    application_url: str | None
    deadline: datetime | None
    status: OpportunityStatus
    created_at: datetime
    updated_at: datetime


class OpportunityApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cover_note: str | None = Field(default=None, max_length=5000)


class OpportunityApplicationReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: OpportunityApplicationStatus

    @model_validator(mode="after")
    def validate_review_status(self):
        if self.status not in {OpportunityApplicationStatus.ACCEPTED, OpportunityApplicationStatus.REJECTED}:
            raise ValueError("Applications may only be accepted or rejected during review.")
        return self


class OpportunityApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    opportunity_id: UUID
    applicant_id: UUID
    status: OpportunityApplicationStatus
    cover_note: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
