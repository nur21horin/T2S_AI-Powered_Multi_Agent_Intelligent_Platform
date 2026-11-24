"""Resource ownership checks, deliberately separate from role permissions."""
from uuid import UUID

from app.core.exceptions import ForbiddenError


def require_resource_owner(actor_id: UUID, owner_id: UUID) -> None:
    """Deny access unless the authenticated actor owns the resource.

    Administrators do not bypass this check. An admin operation that needs
    cross-owner access must pass its own explicit permission check separately.
    """
    if actor_id != owner_id:
        raise ForbiddenError()
