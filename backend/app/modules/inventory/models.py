from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Index, Numeric, String
from sqlmodel import Field, SQLModel

from app.shared.time import Timestamptz, utc_now


class InventorySnapshot(SQLModel, table=True):
    """Snapshot record capturing stock balance from an external source or ERP."""

    __tablename__ = "inventory_snapshots"
    __table_args__ = (
        Index("ix_inv_snapshots_source_sku", "source_system", "sku"),
        Index("ix_inv_snapshots_captured_at", "captured_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    source_system: str = Field(sa_column=Column(String(64), nullable=False, index=True))
    sku: str = Field(sa_column=Column(String(64), nullable=False, index=True))
    location_id: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    on_hand_qty: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(14, 2), nullable=False),
    )
    allocated_qty: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(14, 2), nullable=False),
    )
    available_qty: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(14, 2), nullable=False),
    )
    batch_id: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True, index=True)
    )
    captured_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )
