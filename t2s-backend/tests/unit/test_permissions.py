from types import SimpleNamespace

import pytest

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.security.ownership import require_resource_owner
from app.security.permissions import Permission, has_permission


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER, UserRole.ALUMNI])
def test_roles_without_explicit_admin_grant_are_denied(role):
    assert not has_permission(SimpleNamespace(role=role), Permission.MANAGE_USER_ROLES)


def test_admin_has_only_the_explicit_role_management_permission():
    admin = SimpleNamespace(role=UserRole.ADMIN)

    assert has_permission(admin, Permission.MANAGE_USER_ROLES)
    assert not has_permission(admin, "unregistered.permission")


def test_resource_ownership_is_separate_from_role_permissions():
    owner_id, other_id = object(), object()

    assert require_resource_owner(owner_id, owner_id) is None
    with pytest.raises(ForbiddenError):
        require_resource_owner(other_id, owner_id)
