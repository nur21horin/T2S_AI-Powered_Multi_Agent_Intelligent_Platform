"""Application settings loaded from environment variables / .env (never hardcode secrets)."""
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
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

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
