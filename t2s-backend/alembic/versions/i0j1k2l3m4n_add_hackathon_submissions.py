"""Add Step 6 Phase 3 project-hackathon submissions."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "i0j1k2l3m4n"
down_revision: Union[str, None] = "h9e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    submission_status = sa.Enum("DRAFT", "SUBMITTED", "WITHDRAWN", name="hackathon_submission_status", native_enum=False, create_constraint=True)

    op.create_table(
        "hackathon_submissions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("hackathon_id", uuid, nullable=False),
        sa.Column("project_id", uuid, nullable=False),
        sa.Column("submitter_id", uuid, nullable=False),
        sa.Column("team_id", uuid),
        sa.Column("status", submission_status, server_default="DRAFT", nullable=False),
        sa.Column("repository_url", sa.String(2048)),
        sa.Column("demo_url", sa.String(2048)),
        sa.Column("additional_details", sa.Text()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hackathon_id", "project_id", name="uq_hackathon_submissions_hackathon_project"),
        sa.CheckConstraint("status <> 'SUBMITTED' OR submitted_at IS NOT NULL", name="submitted_timestamp_required"),
        sa.CheckConstraint("status <> 'WITHDRAWN' OR withdrawn_at IS NOT NULL", name="withdrawn_timestamp_required"),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_hackathon_submissions_hackathon_status", "hackathon_submissions", ["hackathon_id", "status"])
    op.create_index("ix_hackathon_submissions_submitter", "hackathon_submissions", ["submitter_id"])
    op.create_index("ix_hackathon_submissions_team", "hackathon_submissions", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_hackathon_submissions_team", table_name="hackathon_submissions")
    op.drop_index("ix_hackathon_submissions_submitter", table_name="hackathon_submissions")
    op.drop_index("ix_hackathon_submissions_hackathon_status", table_name="hackathon_submissions")
    op.drop_table("hackathon_submissions")
