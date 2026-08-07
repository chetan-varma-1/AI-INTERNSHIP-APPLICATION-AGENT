"""Create jobs table for scraped internship listings.

Revision ID: 20260805_0002
Revises: 20260730_0001
Create Date: 2026-08-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260805_0002"
down_revision: str | None = "20260730_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the jobs table."""
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "required_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("salary", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("type", sa.String(length=80), nullable=False, server_default="internship"),
        sa.Column("role", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="mock"),
        sa.Column("duration", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("apply_url", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_company", "jobs", ["company"], unique=False)
    op.create_index("ix_jobs_source", "jobs", ["source"], unique=False)


def downgrade() -> None:
    """Drop the jobs table."""
    op.drop_index("ix_jobs_source", table_name="jobs")
    op.drop_index("ix_jobs_company", table_name="jobs")
    op.drop_table("jobs")
