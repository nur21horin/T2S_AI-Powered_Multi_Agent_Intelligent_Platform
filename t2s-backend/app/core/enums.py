from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ALUMNI = "ALUMNI"
    ADMIN = "ADMIN"


class AuthTokenPurpose(StrEnum):
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class RoomVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class MembershipRole(StrEnum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class MembershipRequestStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class TaskDifficulty(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class TaskStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class SubmissionStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    EVALUATED = "EVALUATED"
    RETURNED = "RETURNED"


class EvaluationStatus(StrEnum):
    FINALIZED = "FINALIZED"
    RETURNED = "RETURNED"
