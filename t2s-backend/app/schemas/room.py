from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import MembershipRequestStatus, MembershipRole, RoomVisibility


class RoomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    topic: str | None = Field(default=None, max_length=120)
    visibility: RoomVisibility = RoomVisibility.PUBLIC


class RoomUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    topic: str | None = Field(default=None, max_length=120)
    visibility: RoomVisibility | None = None


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    name: str
    slug: str
    description: str | None
    topic: str | None
    visibility: RoomVisibility
    is_archived: bool


class MembershipRead(BaseModel):
    id: UUID
    room_id: UUID
    user_id: UUID
    role: MembershipRole
    is_active: bool


class MembershipRequestRead(BaseModel):
    id: UUID
    room_id: UUID
    user_id: UUID
    status: MembershipRequestStatus
