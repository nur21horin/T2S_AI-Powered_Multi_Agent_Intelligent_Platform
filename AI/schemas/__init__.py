"""AI schemas package."""
from AI.schemas.base import BaseRequest, BaseResponse, AgentResponse, ErrorResponse, TypedAgentResponse
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

__all__ = [
    "BaseRequest",
    "BaseResponse",
    "AgentResponse",
    "ErrorResponse",
    "TypedAgentResponse",
    "StudentProfileInput",
    "SkillAssessment",
    "SkillGap",
    "RecommendedSkill",
    "LearningRoadmapStep",
    "ProfileAnalysisResult",
    "ProfileSkillRequest",
    "ProfileSkillResponse",
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