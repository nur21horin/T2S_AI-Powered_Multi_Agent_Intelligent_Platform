from datetime import UTC
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.enums import NotificationType
from app.core.exceptions import NotFoundError
from app.services.notification_service import NotificationService


def test_create_notification_is_server_owned():
    db = Mock()
    recipient_id = uuid4()
    notification = NotificationService(db).create(
        recipient_id=recipient_id,
        notification_type=NotificationType.OPPORTUNITY_APPLICATION_RECEIVED,
        title="New application",
        body="A new application was submitted.",
    )
    assert notification.recipient_id == recipient_id
    assert notification.actor_id is None
    db.add.assert_called_once_with(notification)
    db.flush.assert_called_once()


def test_mark_read_only_updates_recipient_notification():
    recipient_id = uuid4()
    notification = SimpleNamespace(read_at=None)
    db = Mock()
    db.scalar.return_value = notification
    NotificationService(db).mark_read(recipient_id, uuid4())
    assert notification.read_at is not None
    assert notification.read_at.tzinfo == UTC
    db.commit.assert_called_once()


def test_mark_read_hides_other_users_notifications():
    db = Mock()
    db.scalar.return_value = None
    with pytest.raises(NotFoundError):
        NotificationService(db).mark_read(uuid4(), uuid4())
    db.commit.assert_not_called()


def test_unread_count_returns_database_count():
    db = Mock()
    db.scalar.return_value = 3
    result = NotificationService(db).unread_count(uuid4())
    assert result.unread_count == 3


def test_unread_count_normalizes_null_count():
    db = Mock()
    db.scalar.return_value = None
    assert NotificationService(db).unread_count(uuid4()).unread_count == 0


def test_mark_all_read_commits_recipient_scoped_update():
    db = Mock()
    NotificationService(db).mark_all_read(uuid4())
    db.execute.assert_called_once()
    db.commit.assert_called_once()
