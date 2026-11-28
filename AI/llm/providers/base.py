"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from AI.exceptions import LLMProviderError


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    @abstractmethod
    def _create_client(self) -> Any:
        """Create and return the LLM client instance."""
        pass

    @property
    def client(self) -> Any:
        """Lazy initialization of the LLM client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @abstractmethod
    def invoke(self, messages: list[BaseMessage]) -> LLMResult:
        """Invoke the LLM with messages and return result."""
        pass

    @abstractmethod
    async def ainvoke(self, messages: list[BaseMessage]) -> LLMResult:
        """Async invoke the LLM with messages and return result."""
        pass

    def invoke_text(self, messages: list[BaseMessage]) -> str:
        """Invoke LLM and return text content directly."""
        try:
            result = self.invoke(messages)
            if result.generations and result.generations[0]:
                return result.generations[0][0].text
            return ""
        except Exception as e:
            raise LLMProviderError(
                f"Failed to invoke LLM: {str(e)}",
                provider=self.__class__.__name__,
                details={"model": self.model}
            ) from e

    async def ainvoke_text(self, messages: list[BaseMessage]) -> str:
        """Async invoke LLM and return text content directly."""
        try:
            result = await self.ainvoke(messages)
            if result.generations and result.generations[0]:
                return result.generations[0][0].text
            return ""
        except Exception as e:
            raise LLMProviderError(
                f"Failed to invoke LLM: {str(e)}",
                provider=self.__class__.__name__,
                details={"model": self.model}
            ) from e