from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenError
from app.security.ownership import require_resource_owner


def test_cross_user_private_resource_access_is_denied():
    owner, requester = uuid4(), uuid4()

    with pytest.raises(ForbiddenError):
        require_resource_owner(requester, owner)


def test_owner_can_access_own_private_resource():
    owner = uuid4()

    require_resource_owner(owner, owner)
