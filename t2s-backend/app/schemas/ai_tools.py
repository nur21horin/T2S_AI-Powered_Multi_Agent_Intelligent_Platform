from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import OpportunityType, TaskDifficulty, TaskStatus
from app.schemas.progress import ProgressRead


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PageInput(ToolInput):
    page: int = Field(default=1, ge=1, le=1000)
    limit: int = Field(default=20, ge=1, le=100)


class ProfileInput(ToolInput):
    pass


class TaskQueryInput(PageInput):
    room_id: UUID | None = None


class TaskSearchInput(TaskQueryInput):
    query: str = Field(min_length=1, max_length=160)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value):
        if not value.strip():
            raise ValueError("query must contain non-whitespace characters")
        return value.strip()


class AssignedTaskInput(PageInput):
    room_id: UUID | None = None


class CandidateSearchInput(PageInput):
    skills: list[str] = Field(default_factory=list, max_length=20)
    query: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value):
        if value is not None and not value.strip():
            raise ValueError("query must contain non-whitespace characters")
        return value.strip() if value is not None else None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, values):
        result = [value.strip() for value in values]
        if any(not value or len(value) > 80 for value in result):
            raise ValueError("skills must be non-empty and at most 80 characters")
        return result

    @model_validator(mode="after")
    def require_filter(self):
        if not self.skills and not self.query:
            raise ValueError("At least one skill or search query is required.")
        return self


class ProjectInput(ToolInput):
    project_id: UUID


class OpportunityListInput(PageInput):
    opportunity_type: OpportunityType | None = None


class OpportunityQueryInput(OpportunityListInput):
    query: str | None = Field(default=None, min_length=1, max_length=160)
    skills: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value):
        if value is not None and not value.strip():
            raise ValueError("query must contain non-whitespace characters")
        return value.strip() if value is not None else None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, values):
        result = [value.strip() for value in values]
        if any(not value or len(value) > 80 for value in result):
            raise ValueError("skills must be non-empty and at most 80 characters")
        return result


class ResearchQueryInput(PageInput):
    query: str | None = Field(default=None, min_length=1, max_length=160)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value):
        if value is not None and not value.strip():
            raise ValueError("query must contain non-whitespace characters")
        return value.strip() if value is not None else None


class ResourceQueryInput(PageInput):
    query: str = Field(min_length=1, max_length=500)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value):
        if not value.strip():
            raise ValueError("query must contain non-whitespace characters")
        return value.strip()


class ToolError(BaseModel):
    code: str
    message: str


class ToolResult(BaseModel):
    success: bool = True
    data: Any = None
    error: ToolError | None = None
    explanation: str | None = None


class StudentProfileData(BaseModel):
    user_id: UUID
    role: str
    profile_type: str | None = None
    profile: dict[str, object] | None = None


class StudentSkillsData(BaseModel):
    skills: list[str]
    interests: list[str]


class CandidateData(BaseModel):
    user_id: UUID
    department: str | None = None
    skills: list[str]
    matching_skills: list[str]


class TaskData(BaseModel):
    id: UUID
    room_id: UUID
    title: str
    description: str | None = None
    difficulty: TaskDifficulty
    status: TaskStatus
    starts_at: datetime | None = None
    due_at: datetime | None = None


class OpportunityData(BaseModel):
    id: UUID
    title: str
    description: str
    opportunity_type: OpportunityType
    organization: str
    location: str | None = None
    application_url: str | None = None
    deadline: datetime | None = None
    matching_skills: list[str] = Field(default_factory=list)


class ProjectRequirementsData(BaseModel):
    project_id: UUID
    title: str
    description: str | None = None
    objectives: str | None = None
    project_type: str | None = None
    requirements: list[str]


class ResourceData(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    url: str | None = None


class ProgressData(ProgressRead):
    pass
