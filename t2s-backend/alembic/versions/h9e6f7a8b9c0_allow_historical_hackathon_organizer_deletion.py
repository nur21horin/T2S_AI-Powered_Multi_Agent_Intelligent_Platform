"""Preserve hackathons when an organizer account is deleted."""

from typing import Sequence, Union

from alembic import op

revision: str = "h9e6f7a8b9c0"
down_revision: Union[str, None] = "g8d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_hackathons_organizer_id_users", "hackathons", type_="foreignkey")
    op.alter_column("hackathons", "organizer_id", nullable=True)
    op.create_foreign_key("fk_hackathons_organizer_id_users", "hackathons", "users", ["organizer_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_hackathons_organizer_id_users", "hackathons", type_="foreignkey")
    op.alter_column("hackathons", "organizer_id", nullable=False)
    op.create_foreign_key("fk_hackathons_organizer_id_users", "hackathons", "users", ["organizer_id"], ["id"], ondelete="RESTRICT")
