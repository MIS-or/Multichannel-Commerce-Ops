from __future__ import annotations

from typing import Any

from app.shared.errors import AppError


class IntegrationError(AppError):
    """Base exception for all integration and external provider failures."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, status_code=status_code, details=details)


class ProviderConnectionError(IntegrationError):
    """Raised when an external provider cannot be reached (timeout, DNS, connection refused)."""

    def __init__(
        self,
        provider_name: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = {"provider": provider_name, **(details or {})}
        super().__init__(
            code="PROVIDER_CONNECTION_ERROR",
            message=f"Connection to provider '{provider_name}' failed: {message}",
            status_code=504,
            details=merged_details,
        )


class ProviderAuthenticationError(IntegrationError):
    """Raised when external credentials, tokens, or API keys are rejected."""

    def __init__(
        self,
        provider_name: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = {"provider": provider_name, **(details or {})}
        super().__init__(
            code="PROVIDER_AUTH_ERROR",
            message=f"Authentication with provider '{provider_name}' failed: {message}",
            status_code=502,
            details=merged_details,
        )


class ProviderRateLimitError(IntegrationError):
    """Raised when an external platform returns HTTP 429 Too Many Requests."""

    def __init__(
        self,
        provider_name: str,
        retry_after_seconds: int = 60,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = {
            "provider": provider_name,
            "retry_after_seconds": retry_after_seconds,
            **(details or {}),
        }
        super().__init__(
            code="PROVIDER_RATE_LIMIT",
            message=(
                f"Rate limit exceeded on provider '{provider_name}'. "
                f"Retry after {retry_after_seconds}s"
            ),
            status_code=429,
            details=merged_details,
        )
        self.retry_after_seconds = retry_after_seconds


class ProviderPayloadError(IntegrationError):
    """Raised when external data cannot be deserialized or deviates from expected schema."""

    def __init__(
        self,
        provider_name: str,
        message: str,
        *,
        raw_payload: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = {
            "provider": provider_name,
            "raw_payload": str(raw_payload) if raw_payload is not None else None,
            **(details or {}),
        }
        super().__init__(
            code="PROVIDER_PAYLOAD_ERROR",
            message=f"Invalid payload received from provider '{provider_name}': {message}",
            status_code=502,
            details=merged_details,
        )
