"""create automation rules and executions tables

Revision ID: 0009_automation_rules
Revises: 0008_operational_exceptions
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_automation_rules"
down_revision: str | None = "0008_operational_exceptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("trigger_event", sa.String(length=50), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rules_trigger_active_priority",
        "automation_rules",
        ["trigger_event", "is_active", "priority"],
        unique=False,
    )
    op.create_index(
        "ix_rules_created_at",
        "automation_rules",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "automation_rule_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("trigger_event", sa.String(length=50), nullable=False),
        sa.Column("matched", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload_snapshot", sa.JSON(), nullable=False),
        sa.Column("actions_taken", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["automation_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rule_executions_rule_status",
        "automation_rule_executions",
        ["rule_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_rule_executions_executed_at",
        "automation_rule_executions",
        ["executed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rule_executions_executed_at", table_name="automation_rule_executions")
    op.drop_index("ix_rule_executions_rule_status", table_name="automation_rule_executions")
    op.drop_table("automation_rule_executions")
    op.drop_index("ix_rules_created_at", table_name="automation_rules")
    op.drop_index("ix_rules_trigger_active_priority", table_name="automation_rules")
    op.drop_table("automation_rules")
