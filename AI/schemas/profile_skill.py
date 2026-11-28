"""Profile & Skill Agent Pydantic schemas."""
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileInput(BaseModel):
    """Structured student profile input."""
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, description="Student name")
    department: Optional[str] = Field(default=None, description="Academic department")
    major: Optional[str] = Field(default=None, description="Major/specialization")
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=4.0, description="CGPA")
    academic_year: Optional[int] = Field(default=None, ge=1, le=5, description="Academic year")
    skills: list[str] = Field(default_factory=list, description="Current skills")
    interests: list[str] = Field(default_factory=list, description="Areas of interest")
    career_goal: Optional[str] = Field(default=None, description="Career aspiration")
    current_challenges: list[str] = Field(default_factory=list, description="Current learning challenges")
    preferred_learning_style: Optional[str] = Field(default=None, description="Preferred learning style")
    time_availability_hours_per_week: Optional[int] = Field(default=None, ge=1, le=40, description="Hours available per week")


class SkillAssessment(BaseModel):
    """Assessment of a single skill."""
    model_config = ConfigDict(extra="forbid")

    skill: str = Field(description="Skill name")
    proficiency_level: Literal["beginner", "intermediate", "advanced", "expert"] = Field(description="Proficiency level")
    evidence: str = Field(description="Evidence from profile supporting this assessment")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in assessment")


class SkillGap(BaseModel):
    """Identified skill gap."""
    model_config = ConfigDict(extra="forbid")

    skill: str = Field(description="Missing or weak skill")
    importance: Literal["critical", "high", "medium", "low"] = Field(description="Importance for career goal")
    reason: str = Field(description="Why this skill is needed")
    current_level: Optional[Literal["beginner", "intermediate", "advanced", "expert", "none"]] = Field(default="none", description="Current proficiency if any")


class RecommendedSkill(BaseModel):
    """Recommended skill to learn."""
    model_config = ConfigDict(extra="forbid")

    skill: str = Field(description="Recommended skill name")
    category: Literal["technical", "soft", "domain", "tool"] = Field(description="Skill category")
    priority: Literal["immediate", "short_term", "long_term"] = Field(description="Learning priority")
    reason: str = Field(description="Why this skill is recommended")
    suggested_resources: list[str] = Field(default_factory=list, description="Suggested learning resources")
    estimated_weeks: Optional[int] = Field(default=None, ge=1, le=52, description="Estimated weeks to learn")


class LearningRoadmapStep(BaseModel):
    """Single step in learning roadmap."""
    model_config = ConfigDict(extra="forbid")

    step: int = Field(ge=1, description="Step number")
    title: str = Field(description="Step title")
    description: str = Field(description="Detailed description")
    skills_covered: list[str] = Field(default_factory=list, description="Skills covered in this step")
    estimated_weeks: int = Field(ge=1, le=12, description="Estimated weeks to complete")
    prerequisites: list[str] = Field(default_factory=list, description="Prerequisite steps/skills")
    milestones: list[str] = Field(default_factory=list, description="Measurable milestones")


class ProfileAnalysisResult(BaseModel):
    """Complete profile analysis result."""
    model_config = ConfigDict(extra="forbid")

    student_summary: str = Field(description="Brief student profile summary")
    identified_skills: list[SkillAssessment] = Field(default_factory=list, description="Identified skills with assessments")
    strong_skills: list[str] = Field(default_factory=list, description="Strong skill names")
    weak_skills: list[str] = Field(default_factory=list, description="Weak skill names")
    missing_skills: list[SkillGap] = Field(default_factory=list, description="Missing skills for career goal")
    recommended_skills: list[RecommendedSkill] = Field(default_factory=list, description="Recommended skills to learn")
    learning_roadmap: list[LearningRoadmapStep] = Field(default_factory=list, description="Step-by-step learning roadmap")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProfileSkillRequest(BaseModel):
    """Request schema for Profile & Skill Agent."""
    model_config = ConfigDict(extra="forbid")

    student_profile: str = Field(description="Raw student profile text (for backward compatibility)")
    structured_profile: Optional[StudentProfileInput] = Field(default=None, description="Structured profile data")
    force_refresh: bool = Field(default=False, description="Force re-analysis")


class ProfileSkillResponse(BaseModel):
    """Response schema for Profile & Skill Agent."""
    model_config = ConfigDict(extra="forbid")

    success: bool = Field(default=True)
    agent: str = Field(default="ProfileSkillAgent")
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
    result: Optional[ProfileAnalysisResult] = None
    metadata: dict[str, Any] = Field(default_factory=dict)