from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import HackathonParticipationMode, HackathonRegistrationStatus, HackathonRegistrationType, HackathonStatus, HackathonVisibility, UserRole


class HackathonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=20000)
    visibility: HackathonVisibility = HackathonVisibility.PUBLIC
    participation_mode: HackathonParticipationMode = HackathonParticipationMode.BOTH
    start_at: datetime
    end_at: datetime
    registration_start_at: datetime
    registration_end_at: datetime
    participant_limit: int | None = Field(default=None, ge=1, le=1_000_000)
    team_size_min: int = Field(default=1, ge=1, le=1000)
    team_size_max: int = Field(default=1, ge=1, le=1000)
    eligible_roles: list[UserRole] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def validate_dates_and_team_size(self):
        values = (self.start_at, self.end_at, self.registration_start_at, self.registration_end_at)
        if any(value.tzinfo is None for value in values):
            raise ValueError("datetime values must include a timezone")
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        if self.registration_end_at <= self.registration_start_at:
            raise ValueError("registration_end_at must be after registration_start_at")
        if self.registration_end_at > self.start_at:
            raise ValueError("registration must end before the hackathon starts")
        if self.team_size_max < self.team_size_min:
            raise ValueError("team_size_max must be at least team_size_min")
        if self.participation_mode == HackathonParticipationMode.INDIVIDUAL and self.team_size_min != 1:
            raise ValueError("individual hackathons must use team size 1")
        return self


class HackathonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=20000)
    visibility: HackathonVisibility | None = None
    participation_mode: HackathonParticipationMode | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    registration_start_at: datetime | None = None
    registration_end_at: datetime | None = None
    participant_limit: int | None = Field(default=None, ge=1, le=1_000_000)
    team_size_min: int | None = Field(default=None, ge=1, le=1000)
    team_size_max: int | None = Field(default=None, ge=1, le=1000)
    eligible_roles: list[UserRole] | None = Field(default=None, max_length=4)


class HackathonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organizer_id: UUID | None
    title: str
    slug: str
    description: str | None
    status: HackathonStatus
    visibility: HackathonVisibility
    participation_mode: HackathonParticipationMode
    start_at: datetime
    end_at: datetime
    registration_start_at: datetime
    registration_end_at: datetime
    participant_limit: int | None
    team_size_min: int
    team_size_max: int
    published_at: datetime | None
    closed_at: datetime | None
    completed_at: datetime | None
    archived_at: datetime | None


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    hackathon_id: UUID
    registration_type: HackathonRegistrationType
    participant_id: UUID | None
    team_id: UUID | None
    team_name_snapshot: str | None
    status: HackathonRegistrationStatus
    registered_at: datetime
    cancelled_at: datetime | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None


class RegistrationMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    registration_id: UUID
    user_id: UUID | None
    display_name_snapshot: str
    role_snapshot: str | None


class RegistrationDetail(RegistrationRead):
    members: list[RegistrationMemberRead]


class TeamRegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    team_id: UUID
