from __future__ import annotations

from app.modules.auth.dependencies import (
    get_current_user,
    get_strict_user,
    require_permission,
    require_role,
)
from app.modules.auth.errors import (
    ForbiddenError,
    InsufficientPermissionError,
    UnauthorizedError,
)
from app.modules.auth.models import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
    UserContext,
    UserRole,
)

__all__ = [
    "UserRole",
    "Permission",
    "UserContext",
    "ALL_PERMISSIONS",
    "ROLE_PERMISSIONS",
    "get_current_user",
    "get_strict_user",
    "require_role",
    "require_permission",
    "UnauthorizedError",
    "ForbiddenError",
    "InsufficientPermissionError",
]
