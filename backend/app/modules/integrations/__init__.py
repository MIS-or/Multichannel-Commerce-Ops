from __future__ import annotations

from app.modules.integrations.canonical import (
    CanonicalInventoryItem,
    CanonicalOrder,
    CanonicalOrderItem,
    CanonicalOrderStatus,
    CanonicalSettlementEntry,
    CanonicalSettlementStatement,
)
from app.modules.integrations.contracts import (
    BaseConnector,
    ConnectionHealth,
    ConnectionStatus,
    InventoryProvider,
    OrderProvider,
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
    SettlementProvider,
)
from app.modules.integrations.errors import (
    IntegrationError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderPayloadError,
    ProviderRateLimitError,
)
from app.modules.integrations.models import SyncRun, SyncStatus, SyncType
from app.modules.integrations.normalizers import (
    BaseNormalizer,
    ErpNormalizer,
    ShopeeNormalizer,
    TikTokNormalizer,
    get_normalizer_for_channel,
)
from app.modules.integrations.pipeline import NormalizationPipeline
from app.modules.integrations.providers import (
    BaseMockConnector,
    MockErpConnector,
    MockShopeeConnector,
    MockTikTokConnector,
)
from app.modules.integrations.registry import (
    ConnectorRegistry,
    create_default_registry,
    get_connector_registry,
)
from app.modules.integrations.router import router
from app.modules.integrations.schemas import (
    ConnectorHealthStatus,
    IntegrationHealthResponse,
    SyncRunRead,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from app.modules.integrations.service import SyncManagerService

__all__ = [
    # Contracts
    "BaseConnector",
    "ConnectionHealth",
    "ConnectionStatus",
    "InventoryProvider",
    "OrderProvider",
    "RawInventoryBatch",
    "RawOrderBatch",
    "RawSettlementBatch",
    "SettlementProvider",
    # Errors
    "IntegrationError",
    "ProviderAuthenticationError",
    "ProviderConnectionError",
    "ProviderPayloadError",
    "ProviderRateLimitError",
    # Mock Providers
    "BaseMockConnector",
    "MockErpConnector",
    "MockShopeeConnector",
    "MockTikTokConnector",
    # Registry
    "ConnectorRegistry",
    "create_default_registry",
    "get_connector_registry",
    # Canonical Models
    "CanonicalInventoryItem",
    "CanonicalOrder",
    "CanonicalOrderItem",
    "CanonicalOrderStatus",
    "CanonicalSettlementEntry",
    "CanonicalSettlementStatement",
    # Normalizers & Pipeline
    "BaseNormalizer",
    "ErpNormalizer",
    "ShopeeNormalizer",
    "TikTokNormalizer",
    "get_normalizer_for_channel",
    "NormalizationPipeline",
    # Sync Models & Service
    "ConnectorHealthStatus",
    "IntegrationHealthResponse",
    "SyncManagerService",
    "SyncRun",
    "SyncRunRead",
    "SyncStatus",
    "SyncTriggerRequest",
    "SyncTriggerResponse",
    "SyncType",
    "router",
]
