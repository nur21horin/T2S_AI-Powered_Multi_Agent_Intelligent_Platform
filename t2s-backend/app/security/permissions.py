"""Default-deny role and permission checks for API dependencies."""
from collections.abc import Callable
from enum import StrEnum

from fastapi import Depends

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.models.user import User


class Permission(StrEnum):
    MANAGE_USER_ROLES = "admin.users.manage_roles"


_ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.STUDENT: frozenset(),
    UserRole.TEACHER: frozenset(),
    UserRole.ALUMNI: frozenset(),
    UserRole.ADMIN: frozenset({Permission.MANAGE_USER_ROLES}),
}


def has_permission(user: User, permission: Permission) -> bool:
    """Return whether a role has this explicitly granted permission."""
    return permission in _ROLE_PERMISSIONS.get(user.role, frozenset())


def require_permission(permission: Permission) -> Callable[..., User]:
    """Build a dependency that denies access unless the role has this permission."""
    from app.api.deps import get_current_user

    def permission_dependency(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user, permission):
            raise ForbiddenError()
        return user

    return permission_dependency
