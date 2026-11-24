"""Add alumni opportunities and applications."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "j1k2l3m4n5o"
down_revision: Union[str, None] = "i0j1k2l3m4n"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    opportunity_type = sa.Enum("JOB", "INTERNSHIP", "RESEARCH", "MENTORSHIP", name="opportunity_type", native_enum=False, create_constraint=True)
    opportunity_status = sa.Enum("DRAFT", "PUBLISHED", "CLOSED", "ARCHIVED", name="opportunity_status", native_enum=False, create_constraint=True)
    application_status = sa.Enum("PENDING", "ACCEPTED", "REJECTED", "WITHDRAWN", name="opportunity_application_status", native_enum=False, create_constraint=True)

    op.create_table(
        "opportunities",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("owner_id", uuid, nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("opportunity_type", opportunity_type, nullable=False),
        sa.Column("organization", sa.String(160), nullable=False),
        sa.Column("location", sa.String(160)),
        sa.Column("application_url", sa.String(2048)),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("status", opportunity_status, server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(title)) > 0", name="opportunity_title_nonempty"),
        sa.CheckConstraint("length(trim(description)) > 0", name="opportunity_description_nonempty"),
        sa.CheckConstraint("length(trim(organization)) > 0", name="opportunity_organization_nonempty"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_opportunities_status_type_deadline", "opportunities", ["status", "opportunity_type", "deadline"])
    op.create_table(
        "opportunity_applications",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("applicant_id", uuid, nullable=False),
        sa.Column("status", application_status, server_default="PENDING", nullable=False),
        sa.Column("cover_note", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("opportunity_id", "applicant_id", name="uq_opportunity_applications_opportunity_applicant"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_opportunity_applications_applicant_status", "opportunity_applications", ["applicant_id", "status"])
    op.create_index("ix_opportunity_applications_opportunity_status", "opportunity_applications", ["opportunity_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_applications_opportunity_status", table_name="opportunity_applications")
    op.drop_index("ix_opportunity_applications_applicant_status", table_name="opportunity_applications")
    op.drop_table("opportunity_applications")
    op.drop_index("ix_opportunities_status_type_deadline", table_name="opportunities")
    op.drop_table("opportunities")
