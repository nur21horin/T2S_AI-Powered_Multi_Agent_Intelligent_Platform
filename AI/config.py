"""AI module configuration loaded from environment variables."""
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    provider: Literal["groq"] = "groq"
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-20b", alias="GROQ_MODEL")
    temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    max_tokens: Optional[int] = Field(default=None, alias="LLM_MAX_TOKENS")
    timeout: int = Field(default=60, alias="LLM_TIMEOUT")
    max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")


class AISettings(BaseSettings):
    """Main AI module settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    log_level: str = Field(default="INFO", alias="AI_LOG_LEVEL")
    enable_mock_llm: bool = Field(default=False, alias="AI_ENABLE_MOCK_LLM")
    llm: LLMSettings = Field(default_factory=LLMSettings)


@lru_cache
def get_ai_settings() -> AISettings:
    """Get cached AI settings instance."""
    return AISettings()


def clear_settings_cache() -> None:
    """Clear the settings cache for testing."""
    get_ai_settings.cache_clear()