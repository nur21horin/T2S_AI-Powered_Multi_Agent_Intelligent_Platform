from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import TaskDifficulty, TaskStatus


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=10000)
    instructions: str | None = Field(default=None, max_length=20000)
    difficulty: TaskDifficulty = TaskDifficulty.BEGINNER
    starts_at: datetime | None = None
    due_at: datetime | None = None
    max_score: int = Field(default=100, ge=1, le=100000)
    allow_resubmission: bool = False
    max_attempts: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_schedule_and_attempts(self):
        if not self.title.strip():
            raise ValueError("title must contain non-whitespace characters")
        if self.starts_at and self.due_at and self.due_at < self.starts_at:
            raise ValueError("due_at must not be earlier than starts_at")
        if self.allow_resubmission and self.max_attempts is not None and self.max_attempts < 2:
            raise ValueError("resubmission requires at least two attempts")
        if not self.allow_resubmission and self.max_attempts not in (None, 1):
            raise ValueError("max_attempts must be 1 when resubmission is disabled")
        return self

    @field_validator("starts_at", "due_at")
    @classmethod
    def require_timezone(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime values must include a timezone")
        return value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=10000)
    instructions: str | None = Field(default=None, max_length=20000)
    difficulty: TaskDifficulty | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None
    max_score: int | None = Field(default=None, ge=1, le=100000)
    allow_resubmission: bool | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_title_and_schedule(self):
        if self.title is not None and not self.title.strip():
            raise ValueError("title must contain non-whitespace characters")
        if self.starts_at and self.due_at and self.due_at < self.starts_at:
            raise ValueError("due_at must not be earlier than starts_at")
        return self

    @field_validator("starts_at", "due_at")
    @classmethod
    def require_timezone(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime values must include a timezone")
        return value


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    room_id: UUID
    creator_id: UUID
    title: str
    description: str | None
    instructions: str | None
    difficulty: TaskDifficulty
    status: TaskStatus
    starts_at: datetime | None
    due_at: datetime | None
    max_score: int
    allow_resubmission: bool
    max_attempts: int | None
    created_at: datetime
    updated_at: datetime
