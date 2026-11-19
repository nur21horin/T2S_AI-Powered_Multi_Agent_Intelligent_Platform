from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.core.enums import SubmissionStatus


class SubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=100000)
    repository_url: AnyHttpUrl | None = None
    project_url: AnyHttpUrl | None = None

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must contain non-whitespace characters")
        return value


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    user_id: UUID
    content: str
    repository_url: str | None
    project_url: str | None
    attempt_number: int
    status: SubmissionStatus
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
