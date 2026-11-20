"""Add Step 6 Phase 2 hackathons and participation registrations."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "g8d5e6f7a8b9"
down_revision: Union[str, None] = "f7c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    status = sa.Enum("DRAFT", "PUBLISHED", "OPEN", "CLOSED", "COMPLETED", "ARCHIVED", name="hackathon_status", native_enum=False)
    visibility = sa.Enum("PUBLIC", "PRIVATE", name="hackathon_visibility", native_enum=False)
    mode = sa.Enum("INDIVIDUAL", "TEAM", "BOTH", name="hackathon_participation_mode", native_enum=False)
    registration_type = sa.Enum("INDIVIDUAL", "TEAM", name="hackathon_registration_type", native_enum=False)
    registration_status = sa.Enum("PENDING", "APPROVED", "REJECTED", "CANCELLED", name="hackathon_registration_status", native_enum=False)
    user_role = sa.Enum("STUDENT", "TEACHER", "ALUMNI", "ADMIN", name="user_role", native_enum=False)

    op.create_table(
        "hackathons",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("organizer_id", uuid, nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("status", status, server_default="DRAFT", nullable=False),
        sa.Column("visibility", visibility, server_default="PUBLIC", nullable=False),
        sa.Column("participation_mode", mode, server_default="BOTH", nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("participant_limit", sa.Integer()),
        sa.Column("team_size_min", sa.Integer(), server_default="1", nullable=False),
        sa.Column("team_size_max", sa.Integer(), server_default="1", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(title)) > 0", name="title_nonempty"),
        sa.CheckConstraint("participant_limit IS NULL OR participant_limit > 0", name="participant_limit_positive"),
        sa.CheckConstraint("team_size_min >= 1", name="team_size_min_positive"),
        sa.CheckConstraint("team_size_max >= team_size_min", name="team_size_range_valid"),
        sa.CheckConstraint("registration_end_at > registration_start_at", name="registration_window_valid"),
        sa.CheckConstraint("end_at > start_at", name="event_window_valid"),
        sa.CheckConstraint("registration_end_at <= start_at", name="registration_before_event"),
        sa.ForeignKeyConstraint(["organizer_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_hackathons_visibility_status", "hackathons", ["visibility", "status"])

    op.create_table(
        "hackathon_eligible_roles",
        sa.Column("hackathon_id", uuid, nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hackathon_id", "role"),
    )

    op.create_table(
        "hackathon_registrations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("hackathon_id", uuid, nullable=False),
        sa.Column("registration_type", registration_type, nullable=False),
        sa.Column("participant_id", uuid),
        sa.Column("team_id", uuid),
        sa.Column("team_name_snapshot", sa.String(120)),
        sa.Column("status", registration_status, server_default="PENDING", nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by", uuid),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("(registration_type = 'INDIVIDUAL' AND participant_id IS NOT NULL AND team_id IS NULL) OR (registration_type = 'TEAM' AND participant_id IS NULL AND team_id IS NOT NULL)", name="registration_target_valid"),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["participant_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_hackathon_registrations_hackathon_status", "hackathon_registrations", ["hackathon_id", "status"])
    op.create_index("ix_hackathon_registrations_participant", "hackathon_registrations", ["participant_id"])
    op.create_index("ix_hackathon_registrations_team", "hackathon_registrations", ["team_id"])
    op.create_index("ix_hackathon_registrations_individual_unique", "hackathon_registrations", ["hackathon_id", "participant_id"], unique=True, postgresql_where=sa.text("registration_type = 'INDIVIDUAL' AND status <> 'CANCELLED' AND status <> 'REJECTED'"))
    op.create_index("ix_hackathon_registrations_team_unique", "hackathon_registrations", ["hackathon_id", "team_id"], unique=True, postgresql_where=sa.text("registration_type = 'TEAM' AND status <> 'CANCELLED' AND status <> 'REJECTED'"))

    op.create_table(
        "hackathon_registration_members",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("registration_id", uuid, nullable=False),
        sa.Column("user_id", uuid),
        sa.Column("display_name_snapshot", sa.String(120), nullable=False),
        sa.Column("role_snapshot", sa.String(40)),
        sa.ForeignKeyConstraint(["registration_id"], ["hackathon_registrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_hackathon_registration_members_user", "hackathon_registration_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_hackathon_registration_members_user", table_name="hackathon_registration_members")
    op.drop_table("hackathon_registration_members")
    op.drop_index("ix_hackathon_registrations_team_unique", table_name="hackathon_registrations")
    op.drop_index("ix_hackathon_registrations_individual_unique", table_name="hackathon_registrations")
    op.drop_index("ix_hackathon_registrations_team", table_name="hackathon_registrations")
    op.drop_index("ix_hackathon_registrations_participant", table_name="hackathon_registrations")
    op.drop_index("ix_hackathon_registrations_hackathon_status", table_name="hackathon_registrations")
    op.drop_table("hackathon_registrations")
    op.drop_table("hackathon_eligible_roles")
    op.drop_index("ix_hackathons_visibility_status", table_name="hackathons")
    op.drop_table("hackathons")
