"""Structured JSON logging. Never log credentials, tokens or request bodies."""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # Keep privileged audit events on the same structured root pipeline when
    # logging is configured by a standalone CLI as well as by the ASGI app.
    audit_logger = logging.getLogger("app.security.audit")
    audit_logger.disabled = False
    audit_logger.setLevel(root.level)
    audit_logger.propagate = True
    # We emit our own access log line, so silence uvicorn's default one.
    logging.getLogger("uvicorn.access").disabled = True
