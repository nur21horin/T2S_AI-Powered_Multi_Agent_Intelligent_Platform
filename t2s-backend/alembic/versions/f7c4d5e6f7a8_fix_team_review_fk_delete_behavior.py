"""Allow reviewed user deletion while retaining team request history."""

from typing import Sequence, Union

from alembic import op

revision: str = "f7c4d5e6f7a8"
down_revision: Union[str, None] = "f6b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_team_join_requests_reviewed_by_users", "team_join_requests", type_="foreignkey")
    op.create_foreign_key("fk_team_join_requests_reviewed_by_users", "team_join_requests", "users", ["reviewed_by"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_team_join_requests_reviewed_by_users", "team_join_requests", type_="foreignkey")
    op.create_foreign_key("fk_team_join_requests_reviewed_by_users", "team_join_requests", "users", ["reviewed_by"], ["id"])
