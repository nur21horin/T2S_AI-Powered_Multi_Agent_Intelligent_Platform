from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.team import InvitationRead, JoinRequestRead, LeaderUpdate, TeamCreate, TeamMembershipRead, TeamRead, TeamUpdate
from app.services.team_service import TeamService
from app.utils.pagination import Pagination, pagination_params

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).create(user, data)
@router.get("", response_model=list[TeamRead])
def list_teams(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]): return TeamService(db).list(user, page)
@router.get("/owned", response_model=list[TeamRead])
def owned_teams(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]): return TeamService(db).list(user, page, owned=True)
@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).get(user, team_id)
@router.patch("/{team_id}", response_model=TeamRead)
def update_team(team_id: UUID, data: TeamUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).update(user, team_id, data)
@router.post("/{team_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_team(team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): TeamService(db).archive(user, team_id); return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.put("/{team_id}/leader", response_model=TeamMembershipRead)
def set_leader(team_id: UUID, data: LeaderUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).set_leader(user, team_id, data.user_id)
@router.delete("/{team_id}/leader", status_code=status.HTTP_204_NO_CONTENT)
def remove_leader(team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): TeamService(db).set_leader(user, team_id, None); return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.get("/{team_id}/members", response_model=list[TeamMembershipRead])
def members(team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).members(user, team_id)
@router.post("/{team_id}/invitations/{invitee_id}", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
def invite(team_id: UUID, invitee_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).invite(user, team_id, invitee_id)
@router.post("/invitations/{invitation_id}/accept", response_model=InvitationRead)
def accept_invitation(invitation_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).respond_invitation(user, invitation_id, True)
@router.post("/invitations/{invitation_id}/reject", response_model=InvitationRead)
def reject_invitation(invitation_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).respond_invitation(user, invitation_id, False)
@router.post("/{team_id}/join-requests", response_model=JoinRequestRead, status_code=status.HTTP_201_CREATED)
def request_join(team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).request_join(user, team_id)
@router.post("/{team_id}/join-requests/{request_id}/approve", response_model=JoinRequestRead)
def approve_request(team_id: UUID, request_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).decide_request(user, team_id, request_id, True)
@router.post("/{team_id}/join-requests/{request_id}/reject", response_model=JoinRequestRead)
def reject_request(team_id: UUID, request_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): return TeamService(db).decide_request(user, team_id, request_id, False)
@router.delete("/{team_id}/membership", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]): TeamService(db).leave(user, team_id); return Response(status_code=status.HTTP_204_NO_CONTENT)
