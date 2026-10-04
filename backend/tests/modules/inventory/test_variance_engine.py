from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.integrations import CanonicalInventoryItem
from app.modules.inventory import DiscrepancyDirection, InventoryService
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService
from app.shared.time import utc_now


@pytest.fixture
def inventory_svc(session: AsyncSession) -> InventoryService:
    prod_svc = ProductService(ProductRepository(session))
    alert_svc = AlertService(session, AlertRepository(session))
    return InventoryService(session, prod_svc, alert_service=alert_svc)


@pytest.mark.asyncio
async def test_record_canonical_snapshots_persists_records(
    inventory_svc: InventoryService, session: AsyncSession
) -> None:
    now = utc_now()
    items = [
        CanonicalInventoryItem(
            sku="MCO-SKU-001",
            source_system="odoo_erp",
            location_id="WH/Stock",
            on_hand_qty=Decimal("150.00"),
            allocated_qty=Decimal("30.00"),
            available_qty=Decimal("120.00"),
            captured_at=now,
        ),
        CanonicalInventoryItem(
            sku="MCO-SKU-001",
            source_system="shopee_vn",
            location_id="VN_WH_1",
            on_hand_qty=Decimal("150.00"),
            allocated_qty=Decimal("10.00"),
            available_qty=Decimal("140.00"),
            captured_at=now,
        ),
    ]

    saved = await inventory_svc.record_canonical_snapshots(items, batch_id="BATCH-001")
    assert len(saved) == 2
    assert saved[0].batch_id == "BATCH-001"
    assert saved[0].available_qty == Decimal("120.00")
    assert saved[1].available_qty == Decimal("140.00")


@pytest.mark.asyncio
async def test_calculate_variances_detects_oversell_and_under_allocation(
    inventory_svc: InventoryService,
) -> None:
    now = utc_now()
    # Ingest ERP physical truth
    erp_items = [
        CanonicalInventoryItem(
            sku="SKU-OVERSELL",
            source_system="odoo_erp",
            on_hand_qty=Decimal("120"),
            available_qty=Decimal("120"),
            captured_at=now,
        ),
        CanonicalInventoryItem(
            sku="SKU-UNDER",
            source_system="odoo_erp",
            on_hand_qty=Decimal("80"),
            available_qty=Decimal("80"),
            captured_at=now,
        ),
        CanonicalInventoryItem(
            sku="SKU-MATCH",
            source_system="odoo_erp",
            on_hand_qty=Decimal("50"),
            available_qty=Decimal("50"),
            captured_at=now,
        ),
    ]
    await inventory_svc.record_canonical_snapshots(erp_items)

    # Ingest Shopee channel reported stock
    shopee_items = [
        CanonicalInventoryItem(
            sku="SKU-OVERSELL",
            source_system="shopee_vn",
            on_hand_qty=Decimal("140"),
            available_qty=Decimal("140"),  # +20 oversell risk!
            captured_at=now,
        ),
        CanonicalInventoryItem(
            sku="SKU-UNDER",
            source_system="shopee_vn",
            on_hand_qty=Decimal("75"),
            available_qty=Decimal("75"),  # -5 under-allocated
            captured_at=now,
        ),
        CanonicalInventoryItem(
            sku="SKU-MATCH",
            source_system="shopee_vn",
            on_hand_qty=Decimal("50"),
            available_qty=Decimal("50"),  # matched
            captured_at=now,
        ),
    ]
    await inventory_svc.record_canonical_snapshots(shopee_items)

    variances = await inventory_svc.calculate_variances("shopee_vn")
    var_map = {v.sku: v for v in variances}

    # 1. Oversell check
    oversell = var_map["SKU-OVERSELL"]
    assert oversell.variance == Decimal("20")
    assert oversell.has_discrepancy is True
    assert oversell.direction == DiscrepancyDirection.OVER_ALLOCATED

    # 2. Under-allocated check
    under = var_map["SKU-UNDER"]
    assert under.variance == Decimal("-5")
    assert under.has_discrepancy is True
    assert under.direction == DiscrepancyDirection.UNDER_ALLOCATED

    # 3. Match check
    match = var_map["SKU-MATCH"]
    assert match.variance == Decimal("0")
    assert match.has_discrepancy is False
    assert match.direction == DiscrepancyDirection.MATCHED


@pytest.mark.asyncio
async def test_detect_discrepancies_triggers_alerts(
    inventory_svc: InventoryService, session: AsyncSession
) -> None:
    now = utc_now()
    await inventory_svc.record_canonical_snapshots(
        [
            CanonicalInventoryItem(
                sku="DANGER-SKU",
                source_system="odoo_erp",
                on_hand_qty=Decimal("10"),
                available_qty=Decimal("10"),
                captured_at=now,
            ),
            CanonicalInventoryItem(
                sku="DANGER-SKU",
                source_system="tiktok_shop_vn",
                on_hand_qty=Decimal("50"),
                available_qty=Decimal("50"),  # +40 oversell!
                captured_at=now,
            ),
        ]
    )

    discrepancies = await inventory_svc.detect_discrepancies("tiktok_shop_vn", trigger_alerts=True)
    assert len(discrepancies) == 1
    assert discrepancies[0].sku == "DANGER-SKU"
    assert discrepancies[0].direction == DiscrepancyDirection.OVER_ALLOCATED

    # Verify alert was created in alerts repository
    alert_repo = AlertRepository(session)
    active_alerts = await alert_repo.list_all(resolved=False)
    danger_alerts = [a for a in active_alerts if "DANGER-SKU" in a.message]
    assert len(danger_alerts) == 1
    assert "OVERSELL RISK" in danger_alerts[0].message
