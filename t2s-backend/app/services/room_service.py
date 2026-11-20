from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import MembershipRequestStatus, MembershipRole, RoomVisibility
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.room import MembershipRequest, RoomMembership, TechnicalRoom
from app.models.user import User
from app.schemas.room import RoomCreate, RoomUpdate


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().casefold()).strip("-")
    if not value:
        raise ConflictError("Room name must contain letters or numbers.")
    return value[:130]


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, owner: User, data: RoomCreate) -> TechnicalRoom:
        room = TechnicalRoom(owner_id=owner.id, name=data.name.strip(), slug=_slug(data.name), description=data.description, topic=data.topic, visibility=data.visibility)
        self.db.add(room)
        try:
            self.db.flush()
            self.db.add(RoomMembership(room_id=room.id, user_id=owner.id, role=MembershipRole.OWNER))
            self.db.commit()
            self.db.refresh(room)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("A room with this name already exists.") from None
        return room

    def get(self, actor: User, room_id: UUID) -> TechnicalRoom:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Room not found.")
        member = self._membership(actor.id, room.id)
        if room.visibility == RoomVisibility.PRIVATE and member is None:
            raise NotFoundError("Room not found.")
        return room

    def list(self, actor: User) -> list[TechnicalRoom]:
        return list(self.db.scalars(select(TechnicalRoom).where(TechnicalRoom.is_archived.is_(False), TechnicalRoom.visibility == RoomVisibility.PUBLIC).order_by(TechnicalRoom.created_at.desc())))

    def owned(self, actor: User) -> list[TechnicalRoom]:
        return list(self.db.scalars(select(TechnicalRoom).where(TechnicalRoom.owner_id == actor.id, TechnicalRoom.is_archived.is_(False)).order_by(TechnicalRoom.created_at.desc())))

    def joined(self, actor: User) -> list[TechnicalRoom]:
        return list(self.db.scalars(select(TechnicalRoom).join(RoomMembership).where(RoomMembership.user_id == actor.id, RoomMembership.is_active.is_(True), TechnicalRoom.is_archived.is_(False)).order_by(TechnicalRoom.created_at.desc())))

    def own_requests(self, actor: User) -> list[MembershipRequest]:
        return list(self.db.scalars(select(MembershipRequest).where(MembershipRequest.user_id == actor.id).order_by(MembershipRequest.created_at.desc())))

    def update(self, actor: User, room_id: UUID, data: RoomUpdate) -> TechnicalRoom:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Room not found.")
        if room.owner_id != actor.id:
            raise ForbiddenError()
        values = data.model_dump(exclude_unset=True)
        if "name" in values:
            if values["name"] is None:
                raise BadRequestError("Room name cannot be null.")
            values["name"] = values["name"].strip()
            values["slug"] = _slug(values["name"])
        if "visibility" in values and values["visibility"] is None:
            raise BadRequestError("Room visibility cannot be null.")
        for key, value in values.items():
            setattr(room, key, value)
        try:
            self.db.commit()
            self.db.refresh(room)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("A room with this name already exists.") from None
        return room

    def archive(self, actor: User, room_id: UUID) -> None:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None:
            raise NotFoundError("Room not found.")
        if room.owner_id != actor.id:
            raise ForbiddenError()
        room.is_archived = True
        self.db.commit()

    def request_join(self, actor: User, room_id: UUID) -> MembershipRequest:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Room not found.")
        if self._membership(actor.id, room.id) is not None:
            raise ConflictError("You are already a member of this room.")
        existing = self.db.scalar(select(MembershipRequest).where(MembershipRequest.room_id == room.id, MembershipRequest.user_id == actor.id, MembershipRequest.status == MembershipRequestStatus.PENDING))
        if existing is not None:
            raise ConflictError("A membership request is already pending.")
        request = MembershipRequest(room_id=room.id, user_id=actor.id)
        self.db.add(request)
        try:
            self.db.commit()
            self.db.refresh(request)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("A membership request is already pending.") from None
        return request

    def decide_request(self, owner: User, room_id: UUID, request_id: UUID, approve: bool) -> MembershipRequest:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.owner_id != owner.id:
            raise ForbiddenError()
        if room.is_archived:
            raise NotFoundError("Room not found.")
        request = self.db.scalar(select(MembershipRequest).where(MembershipRequest.id == request_id, MembershipRequest.room_id == room_id).with_for_update())
        if request is None:
            raise NotFoundError("Membership request not found.")
        if request.status != MembershipRequestStatus.PENDING:
            raise ConflictError("Membership request is no longer pending.")
        request.status = MembershipRequestStatus.APPROVED if approve else MembershipRequestStatus.REJECTED
        request.reviewed_by = owner.id
        request.reviewed_at = datetime.now(UTC)
        if approve:
            membership = self._any_membership(request.user_id, room_id)
            if membership is None:
                self.db.add(RoomMembership(room_id=room_id, user_id=request.user_id, role=MembershipRole.MEMBER))
            elif not membership.is_active:
                membership.is_active = True
                membership.role = MembershipRole.MEMBER
        try:
            self.db.commit()
            self.db.refresh(request)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Membership state changed concurrently.") from None
        return request

    def members(self, actor: User, room_id: UUID) -> list[RoomMembership]:
        room = self.get(actor, room_id)
        if self._membership(actor.id, room.id) is None and room.owner_id != actor.id:
            raise ForbiddenError()
        return list(self.db.scalars(select(RoomMembership).where(RoomMembership.room_id == room_id, RoomMembership.is_active.is_(True))))

    def requests(self, owner: User, room_id: UUID) -> list[MembershipRequest]:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.owner_id != owner.id:
            raise ForbiddenError()
        if room.is_archived:
            raise NotFoundError("Room not found.")
        return list(self.db.scalars(select(MembershipRequest).where(MembershipRequest.room_id == room_id).order_by(MembershipRequest.created_at.desc())))

    def cancel_request(self, actor: User, room_id: UUID, request_id: UUID) -> None:
        request = self.db.scalar(select(MembershipRequest).where(
            MembershipRequest.id == request_id,
            MembershipRequest.room_id == room_id,
            MembershipRequest.user_id == actor.id,
        ))
        if request is None:
            raise NotFoundError("Membership request not found.")
        if request.status != MembershipRequestStatus.PENDING:
            raise ConflictError("Membership request is no longer pending.")
        request.status = MembershipRequestStatus.CANCELLED
        self.db.commit()

    def leave(self, actor: User, room_id: UUID) -> None:
        room = self.db.get(TechnicalRoom, room_id)
        membership = self._membership(actor.id, room_id)
        if room is None or membership is None:
            raise NotFoundError("Membership not found.")
        if room.owner_id == actor.id or membership.role == MembershipRole.OWNER:
            raise ForbiddenError("The room owner cannot leave the room.")
        membership.is_active = False
        self.db.commit()

    def _membership(self, user_id: UUID, room_id: UUID) -> RoomMembership | None:
        return self.db.scalar(select(RoomMembership).where(RoomMembership.user_id == user_id, RoomMembership.room_id == room_id, RoomMembership.is_active.is_(True)))

    def _any_membership(self, user_id: UUID, room_id: UUID) -> RoomMembership | None:
        return self.db.scalar(select(RoomMembership).where(RoomMembership.user_id == user_id, RoomMembership.room_id == room_id).with_for_update())
