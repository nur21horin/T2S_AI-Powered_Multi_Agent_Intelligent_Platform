"""Add opt-in visibility for student candidate skill discovery."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "l3m4n5o6p7q"
down_revision: Union[str, None] = "k2l3m4n5o6p"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("skills_discoverable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "skills_discoverable")
