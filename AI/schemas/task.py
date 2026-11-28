"""Task Agent Pydantic schemas."""
from typing import Any, Literal, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskGenerationInput(BaseModel):
    """Input for task generation."""
    model_config = ConfigDict(extra="forbid")

    student_profile: Optional[str] = Field(default=None, description="Student profile context")
    skill_gaps: list[str] = Field(default_factory=list, description="Skills to address")
    learning_goals: list[str] = Field(default_factory=list, description="Learning objectives")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(default="beginner")
    task_count: int = Field(default=3, ge=1, le=10, description="Number of tasks to generate")
    duration_weeks: Optional[int] = Field(default=None, ge=1, le=52, description="Learning duration")
    preferred_format: Literal["coding", "reading", "project", "quiz", "mixed"] = Field(default="mixed")


class GeneratedTask(BaseModel):
    """A single generated learning task."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique task identifier")
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed task description")
    skill_addressed: str = Field(description="Primary skill this task addresses")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(description="Task difficulty")
    format: Literal["coding", "reading", "project", "quiz"] = Field(description="Task format")
    estimated_hours: int = Field(ge=1, le=40, description="Estimated hours to complete")
    learning_objectives: list[str] = Field(default_factory=list, description="What student will learn")
    prerequisites: list[str] = Field(default_factory=list, description="Required prior knowledge")
    resources: list[str] = Field(default_factory=list, description="Suggested resources")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Completion criteria")
    order: int = Field(ge=1, description="Sequential order in learning path")


class TaskGenerationResult(BaseModel):
    """Result of task generation."""
    model_config = ConfigDict(extra="forbid")

    tasks: list[GeneratedTask] = Field(default_factory=list, description="Generated tasks")
    total_estimated_hours: int = Field(default=0, description="Total hours for all tasks")
    skills_covered: list[str] = Field(default_factory=list, description="All skills addressed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskSubmissionInput(BaseModel):
    """Input for task submission evaluation."""
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(description="Task identifier")
    student_id: Optional[str] = Field(default=None, description="Student identifier")
    submission_content: str = Field(description="Student's submission text/code")
    submission_type: Literal["code", "text", "link", "file"] = Field(default="text")
    time_spent_hours: Optional[float] = Field(default=None, ge=0, description="Time spent")


class TaskEvaluationResult(BaseModel):
    """Result of task submission evaluation."""
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(description="Task identifier")
    score: float = Field(ge=0.0, le=100.0, description="Score out of 100")
    passed: bool = Field(description="Whether submission meets criteria")
    feedback: str = Field(description="Detailed feedback")
    strengths: list[str] = Field(default_factory=list, description="What was done well")
    improvements: list[str] = Field(default_factory=list, description="Areas for improvement")
    criteria_met: dict[str, bool] = Field(default_factory=dict, description="Per-criterion results")
    suggested_next_steps: list[str] = Field(default_factory=list, description="Recommended follow-up")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskProgressInput(BaseModel):
    """Input for progress tracking."""
    model_config = ConfigDict(extra="forbid")

    student_id: str = Field(description="Student identifier")
    task_ids: list[str] = Field(default_factory=list, description="Task IDs to check")
    include_completed: bool = Field(default=True, description="Include completed tasks")


class TaskProgressResult(BaseModel):
    """Result of progress tracking."""
    model_config = ConfigDict(extra="forbid")

    student_id: str = Field(description="Student identifier")
    total_tasks: int = Field(default=0, description="Total assigned tasks")
    completed_tasks: int = Field(default=0, description="Completed tasks")
    in_progress_tasks: int = Field(default=0, description="In-progress tasks")
    not_started_tasks: int = Field(default=0, description="Not started tasks")
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Completion rate")
    skills_progress: dict[str, float] = Field(default_factory=dict, description="Skill completion rates")
    upcoming_tasks: list[str] = Field(default_factory=list, description="Next recommended tasks")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskAgentRequest(BaseModel):
    """Request schema for Task Agent."""
    model_config = ConfigDict(extra="forbid")

    action: Literal["generate", "evaluate", "progress", "feedback"] = Field(description="Action to perform")
    generation_input: Optional[TaskGenerationInput] = Field(default=None)
    evaluation_input: Optional[TaskSubmissionInput] = Field(default=None)
    progress_input: Optional[TaskProgressInput] = Field(default=None)
    force_refresh: bool = Field(default=False)


class TaskAgentResponse(BaseModel):
    """Response schema for Task Agent."""
    model_config = ConfigDict(extra="forbid")

    success: bool = Field(default=True)
    agent: str = Field(default="TaskAgent")
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
    result: Any = Field(default=None, description="Action-specific result")
    metadata: dict[str, Any] = Field(default_factory=dict)