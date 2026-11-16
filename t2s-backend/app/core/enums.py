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
