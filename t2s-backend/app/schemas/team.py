from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import InvitationStatus, JoinRequestStatus, TeamMembershipRole, TeamMembershipStatus, TeamStatus, TeamVisibility


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=10000)
    visibility: TeamVisibility = TeamVisibility.PRIVATE


class TeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=10000)
    visibility: TeamVisibility | None = None
    status: TeamStatus | None = None


class LeaderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    visibility: TeamVisibility
    status: TeamStatus
    created_at: datetime
    updated_at: datetime


class TeamMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    team_id: UUID
    user_id: UUID
    role: TeamMembershipRole
    status: TeamMembershipStatus
    joined_at: datetime
    ended_at: datetime | None


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    team_id: UUID
    invitee_id: UUID
    inviter_id: UUID
    status: InvitationStatus
    expires_at: datetime
    responded_at: datetime | None


class JoinRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    team_id: UUID
    requester_id: UUID
    status: JoinRequestStatus
    reviewed_by: UUID | None
    reviewed_at: datetime | None
