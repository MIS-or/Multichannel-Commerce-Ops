"""create operational exceptions table

Revision ID: 0008_operational_exceptions
Revises: 0007_inventory_snapshots
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_operational_exceptions"
down_revision: str | None = "0007_inventory_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "operational_exceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reference_id", sa.String(length=100), nullable=False),
        sa.Column("channel_code", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("variance_amount", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("payload_snapshot", sa.JSON(), nullable=False),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("root_cause", sa.String(length=40), nullable=True),
        sa.Column("resolution_notes", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_exceptions_status_domain",
        "operational_exceptions",
        ["status", "domain"],
        unique=False,
    )
    op.create_index(
        "ix_exceptions_reference_id",
        "operational_exceptions",
        ["reference_id"],
        unique=False,
    )
    op.create_index(
        "ix_exceptions_created_at",
        "operational_exceptions",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_exceptions_created_at", table_name="operational_exceptions")
    op.drop_index("ix_exceptions_reference_id", table_name="operational_exceptions")
    op.drop_index("ix_exceptions_status_domain", table_name="operational_exceptions")
    op.drop_table("operational_exceptions")
