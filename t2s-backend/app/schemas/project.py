from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ProjectStatus, ProjectVisibility


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=10000)
    objectives: str | None = Field(default=None, max_length=10000)
    project_type: str | None = Field(default=None, max_length=80)
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=10000)
    objectives: str | None = Field(default=None, max_length=10000)
    project_type: str | None = Field(default=None, max_length=80)
    visibility: ProjectVisibility | None = None
    status: ProjectStatus | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    team_id: UUID | None
    title: str
    description: str | None
    objectives: str | None
    project_type: str | None
    visibility: ProjectVisibility
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
