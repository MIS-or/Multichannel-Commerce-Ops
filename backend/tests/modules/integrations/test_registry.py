from __future__ import annotations

import pytest

from app.modules.integrations import (
    ConnectorRegistry,
    IntegrationError,
    InventoryProvider,
    MockErpConnector,
    OrderProvider,
    ProviderConnectionError,
    SettlementProvider,
    create_default_registry,
    get_connector_registry,
)


def test_default_registry_has_core_connectors() -> None:
    registry = create_default_registry()
    connectors = registry.list_connectors()
    assert len(connectors) == 3

    assert registry.has_connector("odoo_erp")
    assert registry.has_connector("shopee_vn")
    assert registry.has_connector("tiktok_shop_vn")


def test_registry_get_connector() -> None:
    registry = create_default_registry()

    erp = registry.get_connector("odoo_erp")
    assert isinstance(erp, MockErpConnector)

    with pytest.raises(ProviderConnectionError) as exc_info:
        registry.get_connector("non_existent_channel")
    assert "non_existent_channel" in str(exc_info.value)


def test_registry_capability_narrowing() -> None:
    registry = create_default_registry()

    # Order provider
    shopee_order = registry.get_order_provider("shopee_vn")
    assert isinstance(shopee_order, OrderProvider)

    # Inventory provider
    erp_inv = registry.get_inventory_provider("odoo_erp")
    assert isinstance(erp_inv, InventoryProvider)

    # Settlement provider
    shopee_settlement = registry.get_settlement_provider("shopee_vn")
    assert isinstance(shopee_settlement, SettlementProvider)

    # ERP does not implement SettlementProvider in our default mock setup
    with pytest.raises(IntegrationError) as exc_info:
        registry.get_settlement_provider("odoo_erp")
    assert exc_info.value.code == "SETTLEMENT_RECONCILIATION_NOT_SUPPORTED"


def test_registry_lifecycle_and_singleton() -> None:
    registry = ConnectorRegistry()
    assert len(registry.list_connectors()) == 0

    dummy_erp = MockErpConnector(channel_code="custom_erp")
    registry.register(dummy_erp)
    assert registry.has_connector("custom_erp")
    assert registry.get_connector("custom_erp") is dummy_erp

    # Unregister
    removed = registry.unregister("custom_erp")
    assert removed is True
    assert not registry.has_connector("custom_erp")

    # Clear
    registry.register(dummy_erp)
    registry.clear()
    assert len(registry.list_connectors()) == 0

    # Global singleton
    global_reg = get_connector_registry()
    assert global_reg.has_connector("shopee_vn")
