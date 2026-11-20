"""Add Step 5 task, submission, and evaluation tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e5a1b2c3d4e5"
down_revision: Union[str, None] = "c4e7a1b2d903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    difficulty = sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="task_difficulty", native_enum=False, create_constraint=True)
    task_status = sa.Enum("DRAFT", "PUBLISHED", "CLOSED", "ARCHIVED", name="task_status", native_enum=False, create_constraint=True)
    submission_status = sa.Enum("SUBMITTED", "UNDER_REVIEW", "EVALUATED", "RETURNED", name="submission_status", native_enum=False, create_constraint=True)
    evaluation_status = sa.Enum("FINALIZED", "RETURNED", name="evaluation_status", native_enum=False, create_constraint=True)

    op.create_table(
        "tasks",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("room_id", uuid, nullable=False),
        sa.Column("creator_id", uuid, nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("instructions", sa.Text()),
        sa.Column("difficulty", difficulty, server_default="BEGINNER", nullable=False),
        sa.Column("status", task_status, server_default="DRAFT", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("max_score", sa.Integer(), server_default="100", nullable=False),
        sa.Column("allow_resubmission", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("max_attempts", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(title)) > 0", name="title_nonempty"),
        sa.CheckConstraint("max_score > 0", name="max_score_positive"),
        sa.CheckConstraint("max_attempts IS NULL OR max_attempts > 0", name="max_attempts_positive"),
        sa.CheckConstraint("due_at IS NULL OR starts_at IS NULL OR due_at >= starts_at", name="valid_schedule"),
        sa.ForeignKeyConstraint(["room_id"], ["technical_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
    )
    op.create_index("ix_tasks_room_status", "tasks", ["room_id", "status"])

    op.create_table(
        "submissions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("task_id", uuid, nullable=False),
        sa.Column("user_id", uuid, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("repository_url", sa.Text()),
        sa.Column("project_url", sa.Text()),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", submission_status, server_default="SUBMITTED", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("attempt_number > 0", name="attempt_positive"),
        sa.CheckConstraint("length(trim(content)) > 0", name="content_nonempty"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("task_id", "user_id", "attempt_number"),
    )
    op.create_index("ix_submissions_task_user", "submissions", ["task_id", "user_id"])

    op.create_table(
        "evaluations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("submission_id", uuid, nullable=False),
        sa.Column("evaluator_id", uuid, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text()),
        sa.Column("status", evaluation_status, server_default="FINALIZED", nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("score >= 0", name="score_nonnegative"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluator_id"], ["users.id"]),
        sa.UniqueConstraint("submission_id"),
    )


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_index("ix_submissions_task_user", table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_tasks_room_status", table_name="tasks")
    op.drop_table("tasks")
