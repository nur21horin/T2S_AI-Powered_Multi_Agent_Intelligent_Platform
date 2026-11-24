from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService
from app.utils.pagination import Pagination, pagination_params

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return ProjectService(db).create(user, data)

@router.get("", response_model=list[ProjectRead])
def list_projects(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return ProjectService(db).list(user, page)

@router.get("/owned", response_model=list[ProjectRead])
def owned_projects(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return ProjectService(db).list(user, page, owned=True)

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return ProjectService(db).get(user, project_id)

@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: UUID, data: ProjectUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return ProjectService(db).update(user, project_id, data)

@router.put("/{project_id}/team/{team_id}", response_model=ProjectRead)
def attach_team(project_id: UUID, team_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return ProjectService(db).attach_team(user, project_id, team_id)

@router.delete("/{project_id}/team", response_model=ProjectRead)
def detach_team(project_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return ProjectService(db).attach_team(user, project_id, None)

@router.post("/{project_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_project(project_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    ProjectService(db).archive(user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
