"""Groq LLM provider implementation."""
from typing import Any, Optional

from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from langchain_groq import ChatGroq

from AI.llm.providers.base import BaseLLMProvider
from AI.exceptions import LLMProviderError


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider using ChatGroq from LangChain."""

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-20b",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "Groq API key is required",
                provider="GroqProvider",
                details={"model": model}
            )
        super().__init__(model, temperature, max_tokens, timeout, max_retries)
        self.api_key = api_key.strip()

    def _create_client(self) -> ChatGroq:
        """Create ChatGroq client."""
        return ChatGroq(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            max_retries=self.max_retries,
            groq_api_key=self.api_key,
        )

    def invoke(self, messages: list[BaseMessage]) -> LLMResult:
        """Invoke Groq LLM with messages."""
        try:
            return self.client.invoke(messages)
        except Exception as e:
            raise LLMProviderError(
                f"Groq invocation failed: {str(e)}",
                provider="GroqProvider",
                details={"model": self.model}
            ) from e

    async def ainvoke(self, messages: list[BaseMessage]) -> LLMResult:
        """Async invoke Groq LLM with messages."""
        try:
            return await self.client.ainvoke(messages)
        except Exception as e:
            raise LLMProviderError(
                f"Groq async invocation failed: {str(e)}",
                provider="GroqProvider",
                details={"model": self.model}
            ) from e