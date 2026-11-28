"""LLM provider factory for creating provider instances."""
from typing import Any, Optional

from AI.config import get_ai_settings, clear_settings_cache
from AI.exceptions import ConfigurationError, LLMProviderError
from AI.llm.providers.base import BaseLLMProvider
from AI.llm.providers.groq import GroqProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing without API calls."""

    def __init__(
        self,
        model: str = "mock-model",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        max_retries: int = 3,
        mock_response: str = "Mock response from LLM",
    ):
        super().__init__(model, temperature, max_tokens, timeout, max_retries)
        self._mock_response = mock_response
        self._call_count = 0
        self._last_messages: list = []

    def _create_client(self) -> Any:
        return None

    def invoke(self, messages: list) -> Any:
        """Return mock response."""
        self._call_count += 1
        self._last_messages = messages
        
        class MockGeneration:
            def __init__(self, text: str):
                self.text = text
        
        class MockLLMResult:
            def __init__(self, text: str):
                self.generations = [[MockGeneration(text)]]
        
        return MockLLMResult(self._mock_response)

    async def ainvoke(self, messages: list) -> Any:
        """Async return mock response."""
        return self.invoke(messages)

    def set_mock_response(self, response: str) -> None:
        """Set the mock response for subsequent calls."""
        self._mock_response = response

    def get_call_count(self) -> int:
        """Get the number of times invoke was called."""
        return self._call_count

    def get_last_messages(self) -> list:
        """Get the last messages passed to invoke."""
        return self._last_messages


class LLMFactory:
    """Factory for creating LLM provider instances."""

    _providers = {
        "groq": GroqProvider,
        "mock": MockLLMProvider,
    }

    def __init__(self):
        self._provider_cache: dict[str, BaseLLMProvider] = {}

    def _get_settings(self):
        """Get fresh settings instance."""
        return get_ai_settings()

    def create_provider(
        self,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Create an LLM provider instance."""
        settings = self._get_settings()
        provider_name = provider_name or settings.llm.provider
        
        if provider_name not in self._providers:
            raise ConfigurationError(
                f"Unknown LLM provider: {provider_name}",
                details={"available": list(self._providers.keys())}
            )

        # Use mock provider if enabled in settings
        if settings.enable_mock_llm or provider_name == "mock":
            mock_response = kwargs.pop("mock_response", "Mock response from LLM")
            return MockLLMProvider(mock_response=mock_response, **kwargs)

        provider_class = self._providers[provider_name]
        
        if provider_name == "groq":
            api_key = kwargs.pop("api_key", None) or settings.llm.groq_api_key
            if not api_key:
                raise ConfigurationError(
                    "GROQ_API_KEY is required for Groq provider",
                    details={"provider": "groq"}
                )
            return provider_class(
                api_key=api_key,
                model=kwargs.pop("model", settings.llm.groq_model),
                temperature=kwargs.pop("temperature", settings.llm.temperature),
                max_tokens=kwargs.pop("max_tokens", settings.llm.max_tokens),
                timeout=kwargs.pop("timeout", settings.llm.timeout),
                max_retries=kwargs.pop("max_retries", settings.llm.max_retries),
            )

        return provider_class(**kwargs)

    def get_provider(
        self,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Get or create a cached provider instance."""
        settings = self._get_settings()
        cache_key = provider_name or settings.llm.provider
        
        if cache_key not in self._provider_cache:
            self._provider_cache[cache_key] = self.create_provider(provider_name, **kwargs)
        
        return self._provider_cache[cache_key]

    def clear_cache(self) -> None:
        """Clear the provider cache."""
        self._provider_cache.clear()

    @classmethod
    def register_provider(cls, name: str, provider_class: type[BaseLLMProvider]) -> None:
        """Register a new provider class."""
        cls._providers[name] = provider_class


# Global factory instance
_llm_factory = LLMFactory()


def get_llm_factory() -> LLMFactory:
    """Get the global LLM factory instance."""
    return _llm_factory