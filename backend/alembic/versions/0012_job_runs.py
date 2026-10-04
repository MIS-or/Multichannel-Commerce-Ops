"""create job runs table

Revision ID: 0012_job_runs
Revises: 0011_audit_logs
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_job_runs"
down_revision: str | None = "0011_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
        sa.Column("enqueued_by", sa.String(length=100), server_default="system", nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("retry_count >= 0", name="ck_job_runs_retry_nonnegative"),
        sa.CheckConstraint("max_retries >= 0", name="ck_job_runs_max_retries_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_runs_status", "job_runs", ["status"], unique=False)
    op.create_index("ix_job_runs_job_type", "job_runs", ["job_type"], unique=False)
    op.create_index("ix_job_runs_created_at", "job_runs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_runs_created_at", table_name="job_runs")
    op.drop_index("ix_job_runs_job_type", table_name="job_runs")
    op.drop_index("ix_job_runs_status", table_name="job_runs")
    op.drop_table("job_runs")
