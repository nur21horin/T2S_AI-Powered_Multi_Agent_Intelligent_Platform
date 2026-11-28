"""Profile & Skill Analysis Agent for T2S platform."""
import json
import uuid
from typing import Any, Optional

from AI.agents.base import BaseAgent
from AI.exceptions import AgentError, ValidationError
from AI.prompts.profile_skill import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from AI.schemas.profile_skill import (
    ProfileAnalysisResult,
    ProfileSkillRequest,
    ProfileSkillResponse,
    StudentProfileInput,
)


class ProfileSkillAgent(BaseAgent):
    """Agent for analyzing student profiles and skills."""

    agent_name = "ProfileSkillAgent"
    agent_description = "Analyzes student profiles, identifies skills, gaps, and recommends learning paths"
    system_prompt = SYSTEM_PROMPT

    def __init__(
        self,
        llm_provider=None,
        provider_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            llm_provider=llm_provider,
            provider_name=provider_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def analyze_profile(self, student_profile: str) -> str:
        """
        Analyze a student profile and return skill analysis (backward compatible).
        
        Args:
            student_profile: Text description of student profile
            
        Returns:
            Formatted skill analysis report (text)
        """
        if not student_profile or not student_profile.strip():
            raise AgentError(
                "Student profile cannot be empty",
                agent_name=self.agent_name
            )
        
        # Use structured analysis internally
        request = ProfileSkillRequest(student_profile=student_profile.strip())
        response = self.process_request(request)
        
        if response.success and response.result:
            return self._format_text_response(response.result)
        else:
            error_msg = response.metadata.get("error", "Unknown error")
            raise AgentError(f"Analysis failed: {error_msg}", agent_name=self.agent_name)

    def analyze_profile_structured(
        self, 
        student_profile: str,
        structured_profile: Optional[StudentProfileInput] = None
    ) -> ProfileAnalysisResult:
        """
        Analyze a student profile and return structured result.
        
        Args:
            student_profile: Text description of student profile
            structured_profile: Optional structured profile data
            
        Returns:
            Structured ProfileAnalysisResult
        """
        if not student_profile or not student_profile.strip():
            raise AgentError(
                "Student profile cannot be empty",
                agent_name=self.agent_name
            )
        
        request = ProfileSkillRequest(
            student_profile=student_profile.strip(),
            structured_profile=structured_profile
        )
        response = self.process_request(request)
        
        if response.success and response.result:
            return response.result
        else:
            error_msg = response.metadata.get("error", "Unknown error")
            raise AgentError(f"Analysis failed: {error_msg}", agent_name=self.agent_name)

    def _process(self, request: ProfileSkillRequest) -> ProfileAnalysisResult:
        """Process structured request and return structured result."""
        # Build user prompt
        structured_data = "Not provided"
        if request.structured_profile:
            structured_data = request.structured_profile.model_dump_json(indent=2)
        
        career_goal = "Not specified"
        if request.structured_profile and request.structured_profile.career_goal:
            career_goal = request.structured_profile.career_goal
        elif "Career Goal:" in request.student_profile:
            # Extract from raw text
            for line in request.student_profile.split("\n"):
                if "Career Goal" in line:
                    career_goal = line.split(":", 1)[1].strip()
                    break
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            raw_profile=request.student_profile,
            structured_profile=structured_data,
            career_goal=career_goal
        )
        
        # Invoke LLM
        try:
            raw_response = self.invoke(user_input=user_prompt)
        except Exception as e:
            raise AgentError(
                f"LLM invocation failed: {str(e)}",
                agent_name=self.agent_name
            ) from e
        
        # Parse JSON response
        try:
            # Try to extract JSON from response (handle potential markdown)
            json_str = self._extract_json(raw_response)
            parsed = json.loads(json_str)
            result = ProfileAnalysisResult.model_validate(parsed)
            return result
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Failed to parse LLM response as JSON: {str(e)}",
                field="llm_response",
                details={"raw_response": raw_response[:500]}
            ) from e
        except Exception as e:
            raise ValidationError(
                f"Response validation failed: {str(e)}",
                field="llm_response",
                details={"raw_response": raw_response[:500]}
            ) from e

    def _extract_json(self, text: str) -> str:
        """Extract JSON from potentially markdown-formatted response."""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()

    def _format_text_response(self, result: ProfileAnalysisResult) -> str:
        """Format structured result as human-readable text (backward compatible)."""
        lines = []
        lines.append("=" * 50)
        lines.append("PROFILE & SKILL ANALYSIS")
        lines.append("=" * 50)
        lines.append("")
        
        # Student Summary
        lines.append("STUDENT PROFILE SUMMARY")
        lines.append("-" * 30)
        lines.append(result.student_summary)
        lines.append("")
        
        # Identified Skills
        lines.append("IDENTIFIED SKILLS")
        lines.append("-" * 30)
        for skill in result.identified_skills:
            lines.append(f"  • {skill.skill}: {skill.proficiency_level} (confidence: {skill.confidence:.0%})")
            lines.append(f"    Evidence: {skill.evidence}")
        lines.append("")
        
        # Strong Skills
        if result.strong_skills:
            lines.append("STRONG SKILLS")
            lines.append("-" * 30)
            for skill in result.strong_skills:
                lines.append(f"  • {skill}")
            lines.append("")
        
        # Weak Skills
        if result.weak_skills:
            lines.append("WEAK SKILLS")
            lines.append("-" * 30)
            for skill in result.weak_skills:
                lines.append(f"  • {skill}")
            lines.append("")
        
        # Missing Skills
        if result.missing_skills:
            lines.append("MISSING SKILLS (for career goal)")
            lines.append("-" * 30)
            for gap in result.missing_skills:
                lines.append(f"  • {gap.skill} [{gap.importance.upper()}]")
                lines.append(f"    Reason: {gap.reason}")
                if gap.current_level != "none":
                    lines.append(f"    Current: {gap.current_level}")
            lines.append("")
        
        # Recommended Skills
        if result.recommended_skills:
            lines.append("RECOMMENDED SKILLS")
            lines.append("-" * 30)
            for rec in result.recommended_skills:
                lines.append(f"  • {rec.skill} ({rec.category}, {rec.priority})")
                lines.append(f"    Reason: {rec.reason}")
                if rec.suggested_resources:
                    lines.append(f"    Resources: {', '.join(rec.suggested_resources[:3])}")
                if rec.estimated_weeks:
                    lines.append(f"    Est. time: {rec.estimated_weeks} weeks")
            lines.append("")
        
        # Learning Roadmap
        if result.learning_roadmap:
            lines.append("LEARNING ROADMAP")
            lines.append("-" * 30)
            for step in result.learning_roadmap:
                lines.append(f"  Step {step.step}: {step.title} ({step.estimated_weeks} weeks)")
                lines.append(f"    {step.description}")
                if step.skills_covered:
                    lines.append(f"    Skills: {', '.join(step.skills_covered)}")
                if step.milestones:
                    lines.append(f"    Milestones: {'; '.join(step.milestones[:2])}")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)

    def process_request(self, request: ProfileSkillRequest) -> ProfileSkillResponse:
        """Process request and return typed response."""
        request_id = str(uuid.uuid4())
        
        try:
            result = self._process(request)
            
            return ProfileSkillResponse(
                success=True,
                agent=self.agent_name,
                request_id=request_id,
                result=result,
                metadata={"analysis_type": "structured" if request.structured_profile else "text"}
            )
        except Exception as e:
            return ProfileSkillResponse(
                success=False,
                agent=self.agent_name,
                request_id=request_id,
                result=None,
                metadata={"error": str(e), "error_type": type(e).__name__}
            )

    def validate_input(self, request: ProfileSkillRequest) -> None:
        """Validate request input."""
        if not request.student_profile or not request.student_profile.strip():
            raise ValidationError("Student profile cannot be empty", field="student_profile")


# Backward compatibility function
def create_profile_skill_agent(**kwargs) -> ProfileSkillAgent:
    """Factory function for backward compatibility."""
    return ProfileSkillAgent(**kwargs)