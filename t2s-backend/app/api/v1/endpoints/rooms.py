from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.room import MembershipRead, MembershipRequestRead, RoomCreate, RoomRead, RoomUpdate
from app.security.permissions import Permission, require_permission
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["technical rooms"])


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(data: RoomCreate, user: Annotated[User, Depends(require_permission(Permission.CREATE_TECHNICAL_ROOM))], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).create(user, data)


@router.get("", response_model=list[RoomRead])
def list_rooms(user: Annotated[User, Depends(require_permission(Permission.VIEW_PUBLIC_ROOMS))], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).list(user)


@router.get("/owned", response_model=list[RoomRead])
def owned_rooms(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).owned(user)


@router.get("/joined", response_model=list[RoomRead])
def joined_rooms(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).joined(user)


@router.get("/join-requests/mine", response_model=list[MembershipRequestRead])
def my_requests(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).own_requests(user)


@router.get("/{room_id}", response_model=RoomRead)
def get_room(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).get(user, room_id)


@router.patch("/{room_id}", response_model=RoomRead)
def update_room(room_id: UUID, data: RoomUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).update(user, room_id, data)


@router.post("/{room_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_room(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    RoomService(db).archive(user, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{room_id}/join-requests", response_model=MembershipRequestRead, status_code=status.HTTP_201_CREATED)
def request_join(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).request_join(user, room_id)


@router.post("/{room_id}/join-requests/{request_id}/approve", response_model=MembershipRequestRead)
def approve_request(room_id: UUID, request_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).decide_request(user, room_id, request_id, True)


@router.post("/{room_id}/join-requests/{request_id}/reject", response_model=MembershipRequestRead)
def reject_request(room_id: UUID, request_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).decide_request(user, room_id, request_id, False)


@router.get("/{room_id}/members", response_model=list[MembershipRead])
def list_members(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).members(user, room_id)


@router.get("/{room_id}/join-requests", response_model=list[MembershipRequestRead])
def list_requests(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return RoomService(db).requests(user, room_id)


@router.delete("/{room_id}/join-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_request(room_id: UUID, request_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    RoomService(db).cancel_request(user, room_id, request_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{room_id}/membership", status_code=status.HTTP_204_NO_CONTENT)
def leave_room(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    RoomService(db).leave(user, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
