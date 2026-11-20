"""Import model modules so all mapped tables register on ``Base.metadata``.

Model modules should import ``Base`` from ``app.db.base`` and refer to related
models by string name in relationships. The base module deliberately does not
import this package, which keeps metadata ownership one-way and avoids cycles.
"""

from app.models.auth_token import AuthToken
from app.models.user import User
from app.models.profile import AlumniProfile, StudentProfile, TeacherProfile
from app.models.room import MembershipRequest, RoomMembership, TechnicalRoom
from app.models.skill import Interest, Skill, UserInterest, UserSkill
from app.models.task import Task
from app.models.submission import Submission
from app.models.evaluation import Evaluation
from app.models.hackathon import Hackathon, HackathonEligibleRole, HackathonRegistration, HackathonRegistrationMember
from app.models.project import Project
from app.models.team import Team, TeamMembership, TeamInvitation, TeamJoinRequest

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
    "AlumniProfile",
    "StudentProfile",
    "TeacherProfile",
    "Interest",
    "Skill",
    "UserInterest",
    "UserSkill",
    "MembershipRequest",
    "RoomMembership",
    "TechnicalRoom",
    "Task",
    "Submission",
    "Evaluation",
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
