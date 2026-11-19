"""Structured security audit events for privileged application actions."""
import logging
from uuid import UUID

logger = logging.getLogger("app.security.audit")


def record_privileged_action(
    *,
    action: str,
    actor_id: UUID | None,
    target_id: UUID | None,
    outcome: str = "success",
    old_role: str | None = None,
    new_role: str | None = None,
) -> None:
    """Emit safe identifiers and a bounded event name; never include credentials."""
    logger.info(
        "privileged_action",
        extra={
            "extra_fields": {
                "event": action,
                "actor_id": str(actor_id) if actor_id else None,
                "target_id": str(target_id) if target_id else None,
                "outcome": outcome,
                "old_role": old_role,
                "new_role": new_role,
            }
        },
    )
