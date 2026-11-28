"""T2S AI-Powered Multi-Agent Intelligent Platform - AI Module."""

from AI.config import AISettings, LLMSettings, get_ai_settings
from AI.exceptions import (
    AIError,
    ConfigurationError,
    LLMProviderError,
    AgentError,
    ToolError,
    ValidationError,
)
from AI.agents.base import BaseAgent
from AI.agents.profile_skill_agent import ProfileSkillAgent
from AI.agents.task_agent import TaskAgent
from AI.llm.factory import LLMFactory, MockLLMProvider, get_llm_factory
from AI.schemas.base import BaseRequest, BaseResponse, AgentResponse, ErrorResponse
from AI.schemas.profile_skill import (
    StudentProfileInput,
    SkillAssessment,
    SkillGap,
    RecommendedSkill,
    LearningRoadmapStep,
    ProfileAnalysisResult,
    ProfileSkillRequest,
    ProfileSkillResponse,
)
from AI.schemas.task import (
    TaskGenerationInput,
    GeneratedTask,
    TaskGenerationResult,
    TaskSubmissionInput,
    TaskEvaluationResult,
    TaskProgressInput,
    TaskProgressResult,
    TaskAgentRequest,
    TaskAgentResponse,
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "AISettings",
    "LLMSettings",
    "get_ai_settings",
    # Exceptions
    "AIError",
    "ConfigurationError",
    "LLMProviderError",
    "AgentError",
    "ToolError",
    "ValidationError",
    # Agents
    "BaseAgent",
    "ProfileSkillAgent",
    "TaskAgent",
    # LLM
    "LLMFactory",
    "MockLLMProvider",
    "get_llm_factory",
    # Schemas
    "BaseRequest",
    "BaseResponse",
    "AgentResponse",
    "ErrorResponse",
    # Profile Skill Schemas
    "StudentProfileInput",
    "SkillAssessment",
    "SkillGap",
    "RecommendedSkill",
    "LearningRoadmapStep",
    "ProfileAnalysisResult",
    "ProfileSkillRequest",
    "ProfileSkillResponse",
    # Task Schemas
    "TaskGenerationInput",
    "GeneratedTask",
    "TaskGenerationResult",
    "TaskSubmissionInput",
    "TaskEvaluationResult",
    "TaskProgressInput",
    "TaskProgressResult",
    "TaskAgentRequest",
    "TaskAgentResponse",
]