from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    department: str | None = Field(default=None, max_length=120)
    academic_year: int | None = Field(default=None, ge=1, le=20)
    semester: str | None = Field(default=None, max_length=60)
    technical_background: str | None = Field(default=None, max_length=5000)
    bio: str | None = Field(default=None, max_length=5000)
    learning_goals: str | None = Field(default=None, max_length=5000)
    skills_discoverable: bool | None = None
    designation: str | None = Field(default=None, max_length=120)
    introduction: str | None = Field(default=None, max_length=5000)
    areas_of_expertise: str | None = Field(default=None, max_length=5000)
    research_interests: str | None = Field(default=None, max_length=5000)
    mentorship_interests: str | None = Field(default=None, max_length=5000)
    graduation_year: int | None = Field(default=None, ge=1900, le=2200)
    graduation_program: str | None = Field(default=None, max_length=120)
    professional_background: str | None = Field(default=None, max_length=5000)
    current_professional_field: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    company: str | None = Field(default=None, max_length=160)
    mentorship_available: bool | None = None


class ProfileRead(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: UUID
    created_at: datetime
    updated_at: datetime
    profile_type: str
    user_id: UUID


class NamedItemsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    names: list[str] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_names(self):
        if any(not name.strip() or len(name.strip()) > 80 for name in self.names):
            raise ValueError("Names must contain 1 to 80 non-whitespace characters.")
        return self


class NamedItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
