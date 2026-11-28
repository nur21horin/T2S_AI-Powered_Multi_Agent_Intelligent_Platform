"""BaseAgent abstract class for all specialized agents."""
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from AI.config import get_ai_settings
from AI.exceptions import AgentError, ConfigurationError
from AI.llm.factory import get_llm_factory
from AI.llm.providers.base import BaseLLMProvider
from AI.schemas.base import AgentResponse, BaseRequest, BaseResponse


class BaseAgent(ABC):
    """Abstract base class for all T2S agents."""

    # Override in subclasses
    agent_name: str = "BaseAgent"
    agent_description: str = "Base agent for T2S platform"
    system_prompt: str = "You are a helpful AI assistant."

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        provider_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Initialize the agent with optional LLM provider override."""
        self._settings = get_ai_settings()
        
        # Use provided provider or create from factory
        if llm_provider is not None:
            self._llm = llm_provider
        else:
            factory = get_llm_factory()
            self._llm = factory.get_provider(
                provider_name=provider_name,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        # Agent-specific initialization
        self._initialize()

    def _initialize(self) -> None:
        """Override for agent-specific initialization."""
        pass

    @property
    def llm(self) -> BaseLLMProvider:
        """Get the LLM provider instance."""
        return self._llm

    def _build_messages(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[BaseMessage]] = None
    ) -> list[BaseMessage]:
        """Build message list for LLM invocation."""
        messages = []
        
        # System prompt
        messages.append(SystemMessage(content=system_prompt or self.system_prompt))
        
        # History (if provided)
        if history:
            messages.extend(history)
        
        # User input
        messages.append(HumanMessage(content=user_input))
        
        return messages

    def invoke(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[BaseMessage]] = None,
        **kwargs
    ) -> str:
        """Invoke the agent with user input and return text response."""
        start_time = time.perf_counter()
        
        try:
            messages = self._build_messages(user_input, system_prompt, history)
            response = self._llm.invoke_text(messages)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return response
            
        except Exception as e:
            raise AgentError(
                f"Agent invocation failed: {str(e)}",
                agent_name=self.agent_name,
                details={"user_input": user_input[:100] if user_input else ""}
            ) from e

    async def ainvoke(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[BaseMessage]] = None,
        **kwargs
    ) -> str:
        """Async invoke the agent with user input."""
        start_time = time.perf_counter()
        
        try:
            messages = self._build_messages(user_input, system_prompt, history)
            response = await self._llm.ainvoke_text(messages)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return response
            
        except Exception as e:
            raise AgentError(
                f"Agent async invocation failed: {str(e)}",
                agent_name=self.agent_name,
                details={"user_input": user_input[:100] if user_input else ""}
            ) from e

    def process_request(self, request: BaseRequest) -> AgentResponse:
        """Process a structured request and return structured response."""
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        
        try:
            result = self._process(request)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return AgentResponse(
                success=True,
                agent=self.agent_name,
                request_id=request_id,
                processing_time_ms=processing_time,
                result=result,
                metadata={"request_type": request.__class__.__name__}
            )
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return AgentResponse(
                success=False,
                agent=self.agent_name,
                request_id=request_id,
                processing_time_ms=processing_time,
                result=None,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_type": request.__class__.__name__
                }
            )

    @abstractmethod
    def _process(self, request: BaseRequest) -> Any:
        """Process the request and return result. Override in subclasses."""
        pass

    def validate_input(self, request: BaseRequest) -> None:
        """Validate request input. Override for custom validation."""
        pass

    def get_agent_info(self) -> dict[str, Any]:
        """Get agent metadata."""
        return {
            "name": self.agent_name,
            "description": self.agent_description,
            "llm_provider": self._llm.__class__.__name__,
            "llm_model": getattr(self._llm, "model", "unknown"),
        }