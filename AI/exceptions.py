"""Custom exceptions for the AI module."""


class AIError(Exception):
    """Base exception for AI module errors."""

    def __init__(self, message: str, code: str = "AI_ERROR", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ConfigurationError(AIError):
    """Raised when AI configuration is invalid or missing."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)


class LLMProviderError(AIError):
    """Raised when LLM provider fails."""

    def __init__(self, message: str, provider: str, details: dict | None = None):
        super().__init__(message, code="LLM_PROVIDER_ERROR", details={"provider": provider, **(details or {})})
        self.provider = provider


class AgentError(AIError):
    """Raised when agent execution fails."""

    def __init__(self, message: str, agent_name: str, details: dict | None = None):
        super().__init__(message, code="AGENT_ERROR", details={"agent": agent_name, **(details or {})})
        self.agent_name = agent_name


class ToolError(AIError):
    """Raised when a tool execution fails."""

    def __init__(self, message: str, tool_name: str, details: dict | None = None):
        super().__init__(message, code="TOOL_ERROR", details={"tool": tool_name, **(details or {})})
        self.tool_name = tool_name


class ValidationError(AIError):
    """Raised when input/output validation fails."""

    def __init__(self, message: str, field: str | None = None, details: dict | None = None):
        super().__init__(message, code="VALIDATION_ERROR", details={"field": field, **(details or {})})
        self.field = field