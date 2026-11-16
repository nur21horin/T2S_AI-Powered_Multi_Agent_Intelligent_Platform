"""Import model modules so all mapped tables register on ``Base.metadata``.

Model modules should import ``Base`` from ``app.db.base`` and refer to related
models by string name in relationships. The base module deliberately does not
import this package, which keeps metadata ownership one-way and avoids cycles.
"""

from app.models.auth_token import AuthToken
from app.models.user import User

from app.models import (
    ai,
    audit_log,
    auth_token,
    evaluation,
    hackathon,
    notification,
    opportunity,
    profile,
    progress,
    project,
    research,
    resource,
    room,
    skill,
    submission,
    task,
    team,
    user,
)

__all__ = [
    "AuthToken",
    "User",
    "ai",
    "audit_log",
    "auth_token",
    "evaluation",
    "hackathon",
    "notification",
    "opportunity",
    "profile",
    "progress",
    "project",
    "research",
    "resource",
    "room",
    "skill",
    "submission",
    "task",
    "team",
    "user",
]
