from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.modules.audit.models import AuditLog
from app.modules.channels.models import Channel
from app.modules.exceptions.models import OperationalException
from app.modules.integrations.models import SyncRun
from app.modules.inventory.models import InventorySnapshot
from app.modules.jobs.models import JobRun
from app.modules.orders.models import Order
from app.modules.products.models import Product
from app.modules.rules.models import Rule
from app.scripts.seed_demo import CHANNELS, PRODUCTS
from app.scripts.seed_operations import seed_operations


def test_seed_matches_mock_fixture_catalog() -> None:
    assert {channel.code for channel in CHANNELS} == {"shopee", "tiktok", "website"}
    assert {product.sku for product in PRODUCTS} == {"TEE-BLK-M", "TEE-WHT-L", "CAP-WHT"}


@pytest.mark.asyncio
async def test_seed_operations_comprehensive_contract(session: AsyncSession) -> None:
    # 1. First run seeds all entities
    await seed_operations(db_session=session)

    channels = (await session.scalars(select(Channel))).all()
    assert len(channels) >= 3

    products = (await session.scalars(select(Product))).all()
    assert len(products) >= 8

    orders = (await session.scalars(select(Order))).all()
    assert len(orders) >= 10

    snaps = (await session.scalars(select(InventorySnapshot))).all()
    assert len(snaps) >= 10
    # Verify ERP source of truth snapshot is present
    erp_snaps = [s for s in snaps if s.source_system == "erp"]
    assert len(erp_snaps) >= 5

    exceptions = (await session.scalars(select(OperationalException))).all()
    assert len(exceptions) >= 3
    # Check severity distribution
    assert any(e.severity == "critical" and e.status == "open" for e in exceptions)
    assert any(e.status == "investigating" for e in exceptions)
    assert any(e.status == "resolved" and e.root_cause is not None for e in exceptions)

    rules = (await session.scalars(select(Rule))).all()
    assert len(rules) >= 2
    assert all(r.is_active for r in rules)

    sync_runs = (await session.scalars(select(SyncRun))).all()
    assert len(sync_runs) >= 5
    assert all(sr.status == "success" for sr in sync_runs)

    audit_logs = (await session.scalars(select(AuditLog))).all()
    assert len(audit_logs) >= 4

    jobs = (await session.scalars(select(JobRun))).all()
    assert len(jobs) >= 4

    # 2. Re-run to verify strict idempotency
    await seed_operations(db_session=session)

    channels_after = (await session.scalars(select(Channel))).all()
    assert len(channels_after) == len(channels)

    exceptions_after = (await session.scalars(select(OperationalException))).all()
    assert len(exceptions_after) == len(exceptions)

    rules_after = (await session.scalars(select(Rule))).all()
    assert len(rules_after) == len(rules)

    audit_logs_after = (await session.scalars(select(AuditLog))).all()
    assert len(audit_logs_after) == len(audit_logs)

    jobs_after = (await session.scalars(select(JobRun))).all()
    assert len(jobs_after) == len(jobs)

