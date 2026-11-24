import json
import logging
from uuid import uuid4

import app.services.audit_service as audit_service
from app.core.logging import JsonFormatter


def test_privileged_audit_event_is_structured_and_excludes_credentials(monkeypatch):
    actor_id, target_id = uuid4(), uuid4()
    captured = {}
    monkeypatch.setattr(
        audit_service.logger,
        "info",
        lambda message, *, extra: captured.update(message=message, fields=extra["extra_fields"]),
    )
    audit_service.record_privileged_action(
        action="admin.user_role.changed",
        actor_id=actor_id,
        target_id=target_id,
        old_role="STUDENT",
        new_role="ADMIN",
    )
    record = logging.makeLogRecord(
        {
            "name": "app.security.audit",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": captured["message"],
            "extra_fields": captured["fields"],
        }
    )
    payload = json.loads(JsonFormatter().format(record))
    assert payload["event"] == "admin.user_role.changed"
    assert payload["actor_id"] == str(actor_id)
    assert payload["target_id"] == str(target_id)
    assert payload["old_role"] == "STUDENT"
    assert payload["new_role"] == "ADMIN"
    assert not {"password", "token", "secret", "credential"} & payload.keys()
