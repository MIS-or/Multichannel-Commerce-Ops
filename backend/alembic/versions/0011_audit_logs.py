"""create audit logs table

Revision ID: 0011_audit_logs
Revises: 0010_sync_runs
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_audit_logs"
down_revision: str | None = "0010_sync_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=False),
        sa.Column("actor_role", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_logs_actor",
        "audit_logs",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_action",
        "audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_entity",
        "audit_logs",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
    op.drop_table("audit_logs")
