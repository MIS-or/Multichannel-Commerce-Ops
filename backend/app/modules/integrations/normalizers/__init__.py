from __future__ import annotations

from app.modules.integrations.errors import IntegrationError
from app.modules.integrations.normalizers.base import BaseNormalizer
from app.modules.integrations.normalizers.erp import ErpNormalizer
from app.modules.integrations.normalizers.shopee import ShopeeNormalizer
from app.modules.integrations.normalizers.tiktok import TikTokNormalizer


def get_normalizer_for_channel(channel_code: str) -> BaseNormalizer:
    """Resolve the appropriate normalizer for a channel or source system."""
    code = channel_code.lower()
    if "shopee" in code:
        return ShopeeNormalizer()
    if "tiktok" in code:
        return TikTokNormalizer()
    if "odoo" in code or "erp" in code:
        return ErpNormalizer()

    raise IntegrationError(
        code="NORMALIZER_NOT_FOUND",
        message=f"No normalizer registered for channel '{channel_code}'",
        status_code=400,
        details={"channel_code": channel_code},
    )


__all__ = [
    "BaseNormalizer",
    "ErpNormalizer",
    "ShopeeNormalizer",
    "TikTokNormalizer",
    "get_normalizer_for_channel",
]
