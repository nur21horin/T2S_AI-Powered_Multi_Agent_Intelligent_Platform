"""Base Pydantic schemas for AI module."""
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseRequest(BaseModel):
    """Base request schema."""
    model_config = ConfigDict(extra="forbid")

    user_id: Optional[UUID] = Field(default=None, description="User ID making the request")
    session_id: Optional[str] = Field(default=None, description="Session ID for context")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class BaseResponse(BaseModel):
    """Base response schema."""
    model_config = ConfigDict(extra="forbid")

    success: bool = Field(default=True, description="Whether the operation succeeded")
    agent: str = Field(description="Name of the agent that processed the request")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time in milliseconds")


class AgentResponse(BaseResponse):
    """Standard agent response with result data."""
    result: Any = Field(description="Agent-specific result data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ErrorResponse(BaseResponse):
    """Error response schema."""
    success: bool = Field(default=False)
    error: str = Field(description="Error message")
    error_code: str = Field(description="Error code")
    details: dict[str, Any] = Field(default_factory=dict, description="Error details")


T = TypeVar("T", bound=BaseModel)


class TypedAgentResponse(BaseResponse, Generic[T]):
    """Typed agent response with structured result."""
    result: T = Field(description="Structured agent result")
    metadata: dict[str, Any] = Field(default_factory=dict)