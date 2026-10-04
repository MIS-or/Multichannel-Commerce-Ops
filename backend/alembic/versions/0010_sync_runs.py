"""create sync runs table

Revision ID: 0010_sync_runs
Revises: 0009_automation_rules
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_sync_runs"
down_revision: str | None = "0009_automation_rules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel_code", sa.String(length=64), nullable=False),
        sa.Column("sync_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("records_fetched", sa.Integer(), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False),
        sa.Column("records_failed", sa.Integer(), nullable=False),
        sa.Column("cursor_value", sa.String(length=100), nullable=True),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sync_runs_channel_type",
        "sync_runs",
        ["channel_code", "sync_type"],
        unique=False,
    )
    op.create_index(
        "ix_sync_runs_started_at",
        "sync_runs",
        ["started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sync_runs_started_at", table_name="sync_runs")
    op.drop_index("ix_sync_runs_channel_type", table_name="sync_runs")
    op.drop_table("sync_runs")
