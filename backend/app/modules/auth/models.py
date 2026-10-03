from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    ADMIN = "admin"
    OPERATIONS = "operations"
    FINANCE = "finance"
    VIEWER = "viewer"


class Permission(StrEnum):
    # Integrations & Sync
    INTEGRATIONS_READ = "integrations:read"
    INTEGRATIONS_WRITE = "integrations:write"

    # Inventory
    INVENTORY_READ = "inventory:read"
    INVENTORY_WRITE = "inventory:write"

    # Exceptions
    EXCEPTIONS_READ = "exceptions:read"
    EXCEPTIONS_WRITE = "exceptions:write"

    # Reconciliation
    RECONCILIATION_READ = "reconciliation:read"
    RECONCILIATION_WRITE = "reconciliation:write"

    # Automation Rules
    RULES_READ = "rules:read"
    RULES_WRITE = "rules:write"

    # Orders & Ledger
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"

    # Alerts
    ALERTS_READ = "alerts:read"
    ALERTS_WRITE = "alerts:write"

    # Reports
    REPORTS_READ = "reports:read"

    # Audit Logs
    AUDIT_READ = "audit:read"

    # Background Jobs
    JOBS_READ = "jobs:read"
    JOBS_WRITE = "jobs:write"


ALL_PERMISSIONS: frozenset[Permission] = frozenset(Permission)

ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ADMIN: ALL_PERMISSIONS,
    UserRole.OPERATIONS: frozenset(
        {
            Permission.INTEGRATIONS_READ,
            Permission.INTEGRATIONS_WRITE,
            Permission.INVENTORY_READ,
            Permission.INVENTORY_WRITE,
            Permission.EXCEPTIONS_READ,
            Permission.EXCEPTIONS_WRITE,
            Permission.RECONCILIATION_READ,
            Permission.RECONCILIATION_WRITE,
            Permission.RULES_READ,
            Permission.RULES_WRITE,
            Permission.ORDERS_READ,
            Permission.ORDERS_WRITE,
            Permission.ALERTS_READ,
            Permission.ALERTS_WRITE,
            Permission.REPORTS_READ,
            Permission.AUDIT_READ,
            Permission.JOBS_READ,
            Permission.JOBS_WRITE,
        }
    ),
    UserRole.FINANCE: frozenset(
        {
            Permission.RECONCILIATION_READ,
            Permission.RECONCILIATION_WRITE,
            Permission.EXCEPTIONS_READ,
            Permission.EXCEPTIONS_WRITE,
            Permission.REPORTS_READ,
            Permission.ORDERS_READ,
            Permission.INVENTORY_READ,
            Permission.INTEGRATIONS_READ,
            Permission.RULES_READ,
            Permission.ALERTS_READ,
            Permission.AUDIT_READ,
            Permission.JOBS_READ,
        }
    ),
    UserRole.VIEWER: frozenset(
        {
            Permission.REPORTS_READ,
            Permission.ORDERS_READ,
            Permission.INVENTORY_READ,
            Permission.RECONCILIATION_READ,
            Permission.EXCEPTIONS_READ,
            Permission.INTEGRATIONS_READ,
            Permission.RULES_READ,
            Permission.ALERTS_READ,
        }
    ),
}


class UserContext(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: UserRole
    permissions: frozenset[Permission] = Field(default_factory=frozenset)

    SYSTEM_USER_ID: ClassVar[str] = "usr_system_default"

    def has_permission(self, permission: Permission) -> bool:
        if self.role == UserRole.ADMIN:
            return True
        return permission in self.permissions

    def has_role(self, *roles: UserRole) -> bool:
        return self.role in roles or self.role == UserRole.ADMIN
