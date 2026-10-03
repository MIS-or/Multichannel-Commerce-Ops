"""create inventory snapshots table

Revision ID: 0007_inventory_snapshots
Revises: 0006_reconciliation
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_inventory_snapshots"
down_revision: str | None = "0006_reconciliation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("location_id", sa.String(length=64), nullable=True),
        sa.Column("on_hand_qty", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("allocated_qty", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("available_qty", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=True),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inv_snapshots_source_sku",
        "inventory_snapshots",
        ["source_system", "sku"],
        unique=False,
    )
    op.create_index(
        "ix_inv_snapshots_captured_at",
        "inventory_snapshots",
        ["captured_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_inv_snapshots_captured_at", table_name="inventory_snapshots")
    op.drop_index("ix_inv_snapshots_source_sku", table_name="inventory_snapshots")
    op.drop_table("inventory_snapshots")
