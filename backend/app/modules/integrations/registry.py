from __future__ import annotations

from typing import TypeVar

from app.modules.integrations.contracts import (
    BaseConnector,
    InventoryProvider,
    OrderProvider,
    SettlementProvider,
)
from app.modules.integrations.errors import (
    IntegrationError,
    ProviderConnectionError,
)
from app.modules.integrations.providers.mock_erp import MockErpConnector
from app.modules.integrations.providers.mock_shopee import MockShopeeConnector
from app.modules.integrations.providers.mock_tiktok import MockTikTokConnector

T = TypeVar("T", bound=BaseConnector)


CHANNEL_ALIASES: dict[str, str] = {
    "shopee": "shopee_vn",
    "tiktok": "tiktok_shop_vn",
    "erp": "odoo_erp",
    "odoo": "odoo_erp",
}


class ConnectorRegistry:
    """Registry maintaining active connector instances indexed by channel_code."""

    def __init__(self) -> None:
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        """Register or replace a connector instance for its channel_code."""
        self._connectors[connector.channel_code] = connector

    def unregister(self, channel_code: str) -> bool:
        """Remove a connector from the registry. Returns True if removed."""
        if channel_code in self._connectors:
            return self._connectors.pop(channel_code, None) is not None
        resolved = CHANNEL_ALIASES.get(channel_code)
        if resolved:
            return self._connectors.pop(resolved, None) is not None
        return False

    def has_connector(self, channel_code: str) -> bool:
        """Check whether a connector is registered for the specified channel."""
        if channel_code in self._connectors:
            return True
        resolved = CHANNEL_ALIASES.get(channel_code)
        return bool(resolved and resolved in self._connectors)

    def get(self, channel_code: str) -> BaseConnector | None:
        """Retrieve connector by channel code or alias, or return None if not found."""
        if channel_code in self._connectors:
            return self._connectors[channel_code]
        resolved = CHANNEL_ALIASES.get(channel_code)
        if resolved:
            return self._connectors.get(resolved)
        return None

    def get_connector(self, channel_code: str) -> BaseConnector:
        """Retrieve the base connector for a channel code."""
        connector = self.get(channel_code)
        if connector is None:
            raise ProviderConnectionError(
                channel_code,
                f"No connector registered for channel '{channel_code}'",
            )
        return connector

    def get_order_provider(self, channel_code: str) -> OrderProvider:
        """Retrieve connector verified to implement the OrderProvider interface."""
        connector = self.get_connector(channel_code)
        if not isinstance(connector, OrderProvider):
            raise IntegrationError(
                code="ORDER_INGESTION_NOT_SUPPORTED",
                message=f"Channel '{channel_code}' does not support order ingestion",
                status_code=400,
                details={"channel_code": channel_code, "platform_type": connector.platform_type},
            )
        return connector

    def get_inventory_provider(self, channel_code: str) -> InventoryProvider:
        """Retrieve connector verified to implement the InventoryProvider interface."""
        connector = self.get_connector(channel_code)
        if not isinstance(connector, InventoryProvider):
            raise IntegrationError(
                code="INVENTORY_SYNC_NOT_SUPPORTED",
                message=f"Channel '{channel_code}' does not support inventory sync",
                status_code=400,
                details={"channel_code": channel_code, "platform_type": connector.platform_type},
            )
        return connector

    def get_settlement_provider(self, channel_code: str) -> SettlementProvider:
        """Retrieve connector verified to implement the SettlementProvider interface."""
        connector = self.get_connector(channel_code)
        if not isinstance(connector, SettlementProvider):
            raise IntegrationError(
                code="SETTLEMENT_RECONCILIATION_NOT_SUPPORTED",
                message=f"Channel '{channel_code}' does not support settlement reconciliation",
                status_code=400,
                details={"channel_code": channel_code, "platform_type": connector.platform_type},
            )
        return connector

    def list_connectors(self) -> list[BaseConnector]:
        """Return all currently registered connectors."""
        return list(self._connectors.values())

    def list_channel_codes(self) -> list[str]:
        """Return all registered channel codes."""
        return list(self._connectors.keys())

    def clear(self) -> None:
        """Clear all registered connectors."""
        self._connectors.clear()


def create_default_registry() -> ConnectorRegistry:
    """Instantiate a registry prepopulated with default development/test mock connectors."""
    registry = ConnectorRegistry()
    registry.register(MockErpConnector())
    registry.register(MockShopeeConnector())
    registry.register(MockTikTokConnector())
    return registry


_registry_instance: ConnectorRegistry | None = None


def get_connector_registry() -> ConnectorRegistry:
    """Return application-wide connector registry singleton."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = create_default_registry()
    return _registry_instance
