"""Application settings loaded from environment variables / .env (never hardcode secrets)."""
from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    app_env: str = "development"  # development | testing | production
    app_name: str = "T2S Backend"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # Comma-separated in the environment, e.g. CORS_ALLOWED_ORIGINS=http://localhost:3000
    cors_allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    trusted_hosts: Annotated[list[str], NoDecode] = ["localhost", "127.0.0.1"]

    # Database. SecretStr keeps the password out of repr()/logs.
    database_url: SecretStr | None = None
    test_database_url: SecretStr | None = None  # used by the test-suite only
    redis_url: SecretStr | None = None
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30  # seconds to wait for a free pooled connection
    db_pool_recycle: int = 1800  # recycle connections older than 30 min
    db_connect_timeout: int = 5  # seconds
    db_statement_timeout_ms: int = 30000

    # Authentication. Secrets remain masked in reprs and settings error output.
    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "t2s-backend"
    jwt_audience: str = "t2s-api"
    access_token_expire_minutes: int = Field(default=15, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    email_token_expire_minutes: int = Field(default=60, gt=0)
    password_reset_token_expire_minutes: int = Field(default=30, gt=0)

    # Refresh and CSRF cookies. Secure is forced on in production by the cookie helper.
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    cookie_path: str = "/api/v1/auth"
    refresh_cookie_name: str = "t2s_refresh"
    csrf_cookie_name: str = "t2s_csrf"

    # SMTP is optional at startup, but auth email workflows fail closed if it is absent.
    frontend_base_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    email_from: str | None = None
    smtp_starttls: bool = True
    smtp_use_ssl: bool = False

    @field_validator("cors_allowed_origins", "trusted_hosts", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def _no_wildcard_origin(cls, value: list[str]) -> list[str]:
        # Credentialed (cookie) requests must never be allowed from arbitrary origins.
        if "*" in value:
            raise ValueError("CORS_ALLOWED_ORIGINS must list explicit origins, not '*'")
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def _only_hmac_sha256(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Only HS256 is currently supported for JWT signing.")
        return value

    @field_validator("cookie_samesite")
    @classmethod
    def _valid_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be lax, strict, or none.")
        return normalized

    @model_validator(mode="after")
    def _production_auth_secrets(self) -> "Settings":
        if self.is_production and (
            self.jwt_secret_key is None
            or len(self.jwt_secret_key.get_secret_value().encode("utf-8")) < 32
        ):
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes in production.")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
