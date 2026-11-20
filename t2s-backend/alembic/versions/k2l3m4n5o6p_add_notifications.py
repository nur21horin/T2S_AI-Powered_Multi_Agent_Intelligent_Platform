"""Add in-app notifications."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "k2l3m4n5o6p"
down_revision: Union[str, None] = "j1k2l3m4n5o"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    notification_type = sa.Enum("OPPORTUNITY_APPLICATION_RECEIVED", "OPPORTUNITY_APPLICATION_REVIEWED", name="notification_type", native_enum=False, create_constraint=True)
    op.create_table(
        "notifications",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("recipient_id", uuid, nullable=False),
        sa.Column("actor_id", uuid),
        sa.Column("related_opportunity_id", uuid),
        sa.Column("notification_type", notification_type, nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_opportunity_id"], ["opportunities.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_notifications_recipient_read_created", "notifications", ["recipient_id", "read_at", "created_at"])
    op.create_index("ix_notifications_related_opportunity", "notifications", ["related_opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_related_opportunity", table_name="notifications")
    op.drop_index("ix_notifications_recipient_read_created", table_name="notifications")
    op.drop_table("notifications")
