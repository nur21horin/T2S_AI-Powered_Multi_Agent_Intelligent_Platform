from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.core.enums import HackathonSubmissionStatus


class HackathonSubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    repository_url: AnyHttpUrl | None = None
    demo_url: AnyHttpUrl | None = None
    additional_details: str | None = Field(default=None, max_length=20000)

    @field_validator("additional_details")
    @classmethod
    def details_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("additional_details must contain non-whitespace characters")
        return value


class HackathonSubmissionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository_url: AnyHttpUrl | None = None
    demo_url: AnyHttpUrl | None = None
    additional_details: str | None = Field(default=None, max_length=20000)

    @field_validator("additional_details")
    @classmethod
    def details_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("additional_details must contain non-whitespace characters")
        return value


class HackathonSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    hackathon_id: UUID
    project_id: UUID
    submitter_id: UUID
    team_id: UUID | None
    status: HackathonSubmissionStatus
    repository_url: str | None
    demo_url: str | None
    additional_details: str | None
    submitted_at: datetime | None
    withdrawn_at: datetime | None
    created_at: datetime
    updated_at: datetime
