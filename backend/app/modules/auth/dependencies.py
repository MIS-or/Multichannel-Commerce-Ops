from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header

from app.modules.auth.errors import ForbiddenError, InsufficientPermissionError, UnauthorizedError
from app.modules.auth.models import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
    UserContext,
    UserRole,
)

DEFAULT_SYSTEM_USER = UserContext(
    user_id=UserContext.SYSTEM_USER_ID,
    email="system@mco.internal",
    full_name="System Default Admin",
    role=UserRole.ADMIN,
    permissions=ALL_PERMISSIONS,
)

KNOWN_API_KEYS: dict[str, UserRole] = {
    "mco-admin-key-dev": UserRole.ADMIN,
    "mco-operations-key-dev": UserRole.OPERATIONS,
    "mco-finance-key-dev": UserRole.FINANCE,
    "mco-viewer-key-dev": UserRole.VIEWER,
}


def _user_from_role(role: UserRole, user_id: str, email: str, name: str) -> UserContext:
    permissions = ROLE_PERMISSIONS.get(role, frozenset())
    return UserContext(
        user_id=user_id,
        email=email,
        full_name=name,
        role=role,
        permissions=permissions,
    )


async def get_current_user(
    x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> UserContext:
    # 1. Check explicit Role Header
    if x_user_role:
        clean_role = x_user_role.strip().lower()
        try:
            role = UserRole(clean_role)
            return _user_from_role(
                role=role,
                user_id=f"usr_{clean_role}",
                email=f"{clean_role}@mco.internal",
                name=f"{clean_role.capitalize()} Operator",
            )
        except ValueError:
            raise UnauthorizedError(
                f"Invalid role provided in X-User-Role: '{x_user_role}'",
                code="INVALID_ROLE_HEADER",
            ) from None

    # 2. Check API Key Header
    if x_api_key:
        clean_key = x_api_key.strip()
        if clean_key in KNOWN_API_KEYS:
            role = KNOWN_API_KEYS[clean_key]
            return _user_from_role(
                role=role,
                user_id=f"usr_apikey_{role.value}",
                email=f"{role.value}.service@mco.internal",
                name=f"{role.value.capitalize()} Service Account",
            )
        raise UnauthorizedError("Invalid API Key provided", code="INVALID_API_KEY")

    # 3. Check Authorization Bearer Header
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip().lower()
            try:
                role = UserRole(token)
                return _user_from_role(
                    role=role,
                    user_id=f"usr_token_{token}",
                    email=f"{token}@mco.internal",
                    name=f"{token.capitalize()} User",
                )
            except ValueError:
                raise UnauthorizedError(
                    "Invalid Bearer token", code="INVALID_BEARER_TOKEN"
                ) from None

    # 4. Fallback for internal / local dev / automated test pipelines
    return DEFAULT_SYSTEM_USER


async def get_strict_user(
    x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> UserContext:
    if not x_user_role and not x_api_key and not authorization:
        raise UnauthorizedError(
            "Authentication credentials are required for this endpoint.",
            code="AUTHENTICATION_REQUIRED",
        )
    return await get_current_user(x_user_role, x_api_key, authorization)


def require_role(*allowed_roles: UserRole) -> Callable[[UserContext], UserContext]:
    def _role_dependency(
        user: Annotated[UserContext, Depends(get_current_user)],
    ) -> UserContext:
        if not user.has_role(*allowed_roles):
            allowed_names = ", ".join(r.value for r in allowed_roles)
            raise ForbiddenError(
                f"Role '{user.role.value}' is not permitted to access this resource. "
                f"Requires one of: [{allowed_names}].",
                details={
                    "user_role": user.role.value,
                    "allowed_roles": [r.value for r in allowed_roles],
                },
            )
        return user

    return _role_dependency


def require_permission(permission: Permission) -> Callable[[UserContext], UserContext]:
    def _permission_dependency(
        user: Annotated[UserContext, Depends(get_current_user)],
    ) -> UserContext:
        if not user.has_permission(permission):
            raise InsufficientPermissionError(
                required_permission=permission.value,
                details={"user_role": user.role.value},
            )
        return user

    return _permission_dependency
