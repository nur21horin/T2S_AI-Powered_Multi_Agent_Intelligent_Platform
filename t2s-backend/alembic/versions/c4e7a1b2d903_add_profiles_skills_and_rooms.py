"""Add Step 4 profiles, skills, interests, rooms, and membership workflow."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4e7a1b2d903"
down_revision: Union[str, None] = "8a6c2f17d4b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    visibility = sa.Enum("PUBLIC", "PRIVATE", name="room_visibility", native_enum=False, create_constraint=True)
    membership_role = sa.Enum("OWNER", "MEMBER", name="membership_role", native_enum=False, create_constraint=True)
    request_status = sa.Enum("PENDING", "APPROVED", "REJECTED", "CANCELLED", name="membership_request_status", native_enum=False, create_constraint=True)
    op.create_table("student_profiles", sa.Column("id", uuid, primary_key=True), sa.Column("user_id", uuid, nullable=False), sa.Column("department", sa.String(120)), sa.Column("academic_year", sa.Integer()), sa.Column("semester", sa.String(60)), sa.Column("technical_background", sa.Text()), sa.Column("bio", sa.Text()), sa.Column("learning_goals", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id"))
    op.create_table("teacher_profiles", sa.Column("id", uuid, primary_key=True), sa.Column("user_id", uuid, nullable=False), sa.Column("department", sa.String(120)), sa.Column("designation", sa.String(120)), sa.Column("introduction", sa.Text()), sa.Column("areas_of_expertise", sa.Text()), sa.Column("research_interests", sa.Text()), sa.Column("mentorship_interests", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id"))
    op.create_table("alumni_profiles", sa.Column("id", uuid, primary_key=True), sa.Column("user_id", uuid, nullable=False), sa.Column("graduation_year", sa.Integer()), sa.Column("graduation_program", sa.String(120)), sa.Column("professional_background", sa.Text()), sa.Column("current_professional_field", sa.String(120)), sa.Column("job_title", sa.String(120)), sa.Column("company", sa.String(160)), sa.Column("bio", sa.Text()), sa.Column("mentorship_available", sa.Boolean(), server_default=sa.false(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id"))
    op.create_table("skills", sa.Column("id", uuid, primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("normalized_name", sa.String(80), nullable=False), sa.UniqueConstraint("normalized_name"))
    op.create_table("interests", sa.Column("id", uuid, primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("normalized_name", sa.String(80), nullable=False), sa.UniqueConstraint("normalized_name"))
    op.create_table("user_skills", sa.Column("user_id", uuid, nullable=False), sa.Column("skill_id", uuid, nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id", "skill_id"))
    op.create_table("user_interests", sa.Column("user_id", uuid, nullable=False), sa.Column("interest_id", uuid, nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["interest_id"], ["interests.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id", "interest_id"))
    op.create_table("technical_rooms", sa.Column("id", uuid, primary_key=True), sa.Column("owner_id", uuid, nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("slug", sa.String(140), nullable=False), sa.Column("description", sa.Text()), sa.Column("topic", sa.String(120)), sa.Column("visibility", visibility, server_default="PUBLIC", nullable=False), sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["owner_id"], ["users.id"]), sa.UniqueConstraint("slug"))
    op.create_table("room_memberships", sa.Column("id", uuid, primary_key=True), sa.Column("room_id", uuid, nullable=False), sa.Column("user_id", uuid, nullable=False), sa.Column("role", membership_role, server_default="MEMBER", nullable=False), sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["room_id"], ["technical_rooms.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("room_id", "user_id"))
    op.create_table("membership_requests", sa.Column("id", uuid, primary_key=True), sa.Column("room_id", uuid, nullable=False), sa.Column("user_id", uuid, nullable=False), sa.Column("status", request_status, server_default="PENDING", nullable=False), sa.Column("reviewed_by", uuid), sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["room_id"], ["technical_rooms.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]))
    op.create_index("ix_membership_requests_pending_unique", "membership_requests", ["room_id", "user_id"], unique=True, postgresql_where=sa.text("status = 'PENDING'"))
    op.create_index("ix_membership_requests_room_status", "membership_requests", ["room_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_membership_requests_room_status", table_name="membership_requests")
    op.drop_index("ix_membership_requests_pending_unique", table_name="membership_requests")
    op.drop_table("membership_requests")
    op.drop_table("room_memberships")
    op.drop_table("technical_rooms")
    op.drop_table("user_interests")
    op.drop_table("user_skills")
    op.drop_table("interests")
    op.drop_table("skills")
    op.drop_table("alumni_profiles")
    op.drop_table("teacher_profiles")
    op.drop_table("student_profiles")
