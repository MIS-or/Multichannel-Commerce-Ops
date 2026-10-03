from typing import Any


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(code=code, message=message, status_code=404, details=details)


class ConflictError(AppError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(code=code, message=message, status_code=409, details=details)


class BusinessRuleError(AppError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(code=code, message=message, status_code=422, details=details)


class UnauthorizedError(AppError):
    def __init__(
        self,
        message: str = "Authentication required",
        *,
        code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, status_code=401, details=details)


class ForbiddenError(AppError):
    def __init__(
        self,
        message: str = "Permission denied",
        *,
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, status_code=403, details=details)
