"""Add Step 6 Phase 1 projects, teams, and collaboration tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f6b3c4d5e6f7"
down_revision: Union[str, None] = "e5a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    enums = {
        "project_visibility": ["PUBLIC", "PRIVATE"], "project_status": ["DRAFT", "ACTIVE", "COMPLETED", "ARCHIVED"],
        "team_visibility": ["PUBLIC", "PRIVATE"], "team_status": ["ACTIVE", "ARCHIVED"],
        "team_membership_role": ["OWNER", "LEADER", "MEMBER"], "team_membership_status": ["ACTIVE", "LEFT", "REMOVED"],
        "team_invitation_status": ["PENDING", "ACCEPTED", "REJECTED", "CANCELLED", "EXPIRED"],
        "team_join_request_status": ["PENDING", "APPROVED", "REJECTED", "WITHDRAWN"],
    }
    for name, values in enums.items():
        sa.Enum(*values, name=name, native_enum=False, create_constraint=True).create(op.get_bind(), checkfirst=True)
    op.create_table("teams", sa.Column("id", uuid, primary_key=True), sa.Column("owner_id", uuid, nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("description", sa.Text()), sa.Column("visibility", sa.Enum(*enums["team_visibility"], name="team_visibility", native_enum=False), server_default="PRIVATE", nullable=False), sa.Column("status", sa.Enum(*enums["team_status"], name="team_status", native_enum=False), server_default="ACTIVE", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"))
    op.create_table("projects", sa.Column("id", uuid, primary_key=True), sa.Column("owner_id", uuid, nullable=False), sa.Column("team_id", uuid), sa.Column("title", sa.String(160), nullable=False), sa.Column("description", sa.Text()), sa.Column("objectives", sa.Text()), sa.Column("project_type", sa.String(80)), sa.Column("visibility", sa.Enum(*enums["project_visibility"], name="project_visibility", native_enum=False), server_default="PRIVATE", nullable=False), sa.Column("status", sa.Enum(*enums["project_status"], name="project_status", native_enum=False), server_default="DRAFT", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("length(trim(title)) > 0", name="title_nonempty"), sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"))
    op.create_index("ix_projects_visibility_status", "projects", ["visibility", "status"])
    op.create_table("team_memberships", sa.Column("id", uuid, primary_key=True), sa.Column("team_id", uuid, nullable=False), sa.Column("user_id", uuid, nullable=False), sa.Column("role", sa.Enum(*enums["team_membership_role"], name="team_membership_role", native_enum=False), server_default="MEMBER", nullable=False), sa.Column("status", sa.Enum(*enums["team_membership_status"], name="team_membership_status", native_enum=False), server_default="ACTIVE", nullable=False), sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"))
    op.create_index("ix_team_memberships_active_unique", "team_memberships", ["team_id", "user_id"], unique=True, postgresql_where=sa.text("status = 'ACTIVE'"))
    op.create_index("ix_team_memberships_team_status", "team_memberships", ["team_id", "status"])
    op.create_index("ix_team_memberships_leader_unique", "team_memberships", ["team_id"], unique=True, postgresql_where=sa.text("status = 'ACTIVE' AND role = 'LEADER'"))
    op.create_table("team_invitations", sa.Column("id", uuid, primary_key=True), sa.Column("team_id", uuid, nullable=False), sa.Column("invitee_id", uuid, nullable=False), sa.Column("inviter_id", uuid, nullable=False), sa.Column("status", sa.Enum(*enums["team_invitation_status"], name="team_invitation_status", native_enum=False), server_default="PENDING", nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("responded_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["invitee_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["inviter_id"], ["users.id"]))
    op.create_index("ix_team_invitations_pending_unique", "team_invitations", ["team_id", "invitee_id"], unique=True, postgresql_where=sa.text("status = 'PENDING'"))
    op.create_table("team_join_requests", sa.Column("id", uuid, primary_key=True), sa.Column("team_id", uuid, nullable=False), sa.Column("requester_id", uuid, nullable=False), sa.Column("status", sa.Enum(*enums["team_join_request_status"], name="team_join_request_status", native_enum=False), server_default="PENDING", nullable=False), sa.Column("reviewed_by", uuid), sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"))
    op.create_index("ix_team_join_requests_pending_unique", "team_join_requests", ["team_id", "requester_id"], unique=True, postgresql_where=sa.text("status = 'PENDING'"))
    op.create_index("ix_team_join_requests_team_status", "team_join_requests", ["team_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_team_join_requests_team_status", table_name="team_join_requests")
    op.drop_index("ix_team_join_requests_pending_unique", table_name="team_join_requests")
    op.drop_table("team_join_requests")
    op.drop_index("ix_team_invitations_pending_unique", table_name="team_invitations")
    op.drop_table("team_invitations")
    op.drop_index("ix_team_memberships_leader_unique", table_name="team_memberships")
    op.drop_index("ix_team_memberships_team_status", table_name="team_memberships")
    op.drop_index("ix_team_memberships_active_unique", table_name="team_memberships")
    op.drop_table("team_memberships")
    op.drop_index("ix_projects_visibility_status", table_name="projects")
    op.drop_table("projects")
    op.drop_table("teams")
    for name in ("team_join_request_status", "team_invitation_status", "team_membership_status", "team_membership_role", "team_status", "team_visibility", "project_status", "project_visibility"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
