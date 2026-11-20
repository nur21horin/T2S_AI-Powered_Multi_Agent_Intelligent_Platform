from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Enum as SAEnum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ProjectStatus, ProjectVisibility
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    objectives: Mapped[str | None] = mapped_column(Text)
    project_type: Mapped[str | None] = mapped_column(String(80))
    visibility: Mapped[ProjectVisibility] = mapped_column(SAEnum(ProjectVisibility, name="project_visibility", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=ProjectVisibility.PRIVATE, server_default=ProjectVisibility.PRIVATE.value)
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus, name="project_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=ProjectStatus.DRAFT, server_default=ProjectStatus.DRAFT.value)
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects")
    team: Mapped["Team | None"] = relationship("Team", back_populates="projects")
    __table_args__ = (CheckConstraint("length(trim(title)) > 0", name="title_nonempty"), Index("ix_projects_visibility_status", "visibility", "status"))
