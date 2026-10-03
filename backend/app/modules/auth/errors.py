from __future__ import annotations

from typing import Any

from app.shared.errors import ForbiddenError, UnauthorizedError

__all__ = ["UnauthorizedError", "ForbiddenError", "InsufficientPermissionError"]


class InsufficientPermissionError(ForbiddenError):
    def __init__(
        self,
        required_permission: str,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        err_details = details or {}
        err_details["required_permission"] = required_permission
        super().__init__(
            message=message or f"Insufficient permissions: requires '{required_permission}'",
            code="FORBIDDEN_INSUFFICIENT_PERMISSION",
            details=err_details,
        )
