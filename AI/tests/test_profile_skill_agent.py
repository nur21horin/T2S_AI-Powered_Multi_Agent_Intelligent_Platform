"""Unit tests for ProfileSkillAgent."""
import pytest
from typing import Any
from unittest.mock import Mock, patch

from AI.agents.profile_skill_agent import ProfileSkillAgent
from AI.exceptions import AgentError, ValidationError
from AI.llm.factory import MockLLMProvider
from AI.schemas.profile_skill import (
    StudentProfileInput,
    ProfileAnalysisResult,
    ProfileSkillRequest,
    SkillAssessment,
    SkillGap,
    RecommendedSkill,
    LearningRoadmapStep,
)


# Sample mock response matching the expected JSON structure
MOCK_STRUCTURED_RESPONSE = """
{
  "student_summary": "Test student with Python and ML skills aiming for Data Science",
  "identified_skills": [
    {"skill": "Python", "proficiency_level": "intermediate", "evidence": "Listed in skills", "confidence": 0.9},
    {"skill": "Machine Learning", "proficiency_level": "beginner", "evidence": "Listed in skills", "confidence": 0.8},
    {"skill": "Pandas", "proficiency_level": "beginner", "evidence": "Listed in skills", "confidence": 0.75}
  ],
  "strong_skills": ["Python"],
  "weak_skills": ["Machine Learning", "Pandas"],
  "missing_skills": [
    {"skill": "Deep Learning", "importance": "critical", "reason": "Required for Data Science role", "current_level": "none"},
    {"skill": "Statistics", "importance": "high", "reason": "Foundation for ML", "current_level": "none"},
    {"skill": "MLOps", "importance": "high", "reason": "Production ML deployment", "current_level": "none"}
  ],
  "recommended_skills": [
    {"skill": "Deep Learning", "category": "technical", "priority": "immediate", "reason": "Core for Data Science", "suggested_resources": ["Deep Learning Book", "Fast.ai"], "estimated_weeks": 8},
    {"skill": "Statistics", "category": "technical", "priority": "immediate", "reason": "Mathematical foundation", "suggested_resources": ["Statistical Learning", "Khan Academy"], "estimated_weeks": 6},
    {"skill": "MLOps", "category": "technical", "priority": "short_term", "reason": "Production deployment", "suggested_resources": ["MLOps Zoomcamp", "Kubeflow docs"], "estimated_weeks": 8}
  ],
  "learning_roadmap": [
    {"step": 1, "title": "Statistics Fundamentals", "description": "Learn probability, distributions, hypothesis testing", "skills_covered": ["Statistics"], "estimated_weeks": 6, "prerequisites": [], "milestones": ["Complete StatQuest playlist", "Pass practice exam"]},
    {"step": 2, "title": "Deep Learning with PyTorch", "description": "Build neural networks for tabular and image data", "skills_covered": ["Deep Learning"], "estimated_weeks": 8, "prerequisites": ["Statistics", "Python"], "milestones": ["Train CNN on CIFAR-10", "Build RNN for text"]},
    {"step": 3, "title": "MLOps Pipeline", "description": "Deploy models with CI/CD, monitoring, retraining", "skills_covered": ["MLOps"], "estimated_weeks": 8, "prerequisites": ["Deep Learning"], "milestones": ["Deploy model to cloud", "Set up monitoring"]}
  ],
  "metadata": {"analysis_version": "1.0", "profile_completeness": 0.8}
}
"""

MOCK_TEXT_RESPONSE = """
==================================================
PROFILE & SKILL ANALYSIS
==================================================

STUDENT PROFILE SUMMARY
------------------------------
Test student with Python and ML skills aiming for Data Science

IDENTIFIED SKILLS
------------------------------
  • Python: intermediate (confidence: 90%)
    Evidence: Listed in skills
  • Machine Learning: beginner (confidence: 80%)
    Evidence: Listed in skills
  • Pandas: beginner (confidence: 75%)
    Evidence: Listed in skills

STRONG SKILLS
------------------------------
  • Python

WEAK SKILLS
------------------------------
  • Machine Learning
  • Pandas

MISSING SKILLS (for career goal)
------------------------------
  • Deep Learning [CRITICAL]
    Reason: Required for Data Science role
  • Statistics [HIGH]
    Reason: Foundation for ML
  • MLOps [HIGH]
    Reason: Production ML deployment

RECOMMENDED SKILLS
------------------------------
  • Deep Learning (technical, immediate)
    Reason: Core for Data Science
    Resources: Deep Learning Book, Fast.ai
    Est. time: 8 weeks
  • Statistics (technical, immediate)
    Reason: Mathematical foundation
    Resources: Statistical Learning, Khan Academy
    Est. time: 6 weeks
  • MLOps (technical, short_term)
    Reason: Production deployment
    Resources: MLOps Zoomcamp, Kubeflow docs
    Est. time: 8 weeks

LEARNING ROADMAP
------------------------------
  Step 1: Statistics Fundamentals (6 weeks)
    Learn probability, distributions, hypothesis testing
    Skills: Statistics
    Milestones: Complete StatQuest playlist; Pass practice exam
  Step 2: Deep Learning with PyTorch (8 weeks)
    Build neural networks for tabular and image data
    Skills: Deep Learning
    Milestones: Train CNN on CIFAR-10; Build RNN for text
  Step 3: MLOps Pipeline (8 weeks)
    Deploy models with CI/CD, monitoring, retraining
    Skills: MLOps
    Milestones: Deploy model to cloud; Set up monitoring

==================================================
"""


class TestProfileSkillAgent:
    """Tests for ProfileSkillAgent."""

    def test_agent_creation(self):
        """Test agent can be created with mock LLM."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE))
        assert agent.agent_name == "ProfileSkillAgent"
        assert "Profile and Skill Analysis" in agent.system_prompt

    def test_analyze_profile_backward_compatible(self):
        """Test original analyze_profile method returns formatted text."""
        mock_llm = MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        student = "Name: Test\nSkills: Python\nCareer Goal: Data Scientist"
        result = agent.analyze_profile(student)
        
        assert isinstance(result, str)
        assert "PROFILE & SKILL ANALYSIS" in result
        assert "STUDENT PROFILE SUMMARY" in result
        assert "Python" in result
        assert "Deep Learning" in result

    def test_analyze_profile_structured(self):
        """Test structured analysis returns ProfileAnalysisResult."""
        mock_llm = MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        student = "Name: Test\nSkills: Python\nCareer Goal: Data Scientist"
        result = agent.analyze_profile_structured(student)
        
        assert isinstance(result, ProfileAnalysisResult)
        assert result.student_summary == "Test student with Python and ML skills aiming for Data Science"
        assert len(result.identified_skills) == 3
        assert result.strong_skills == ["Python"]
        assert result.weak_skills == ["Machine Learning", "Pandas"]
        assert len(result.missing_skills) == 3
        assert len(result.recommended_skills) == 3
        assert len(result.learning_roadmap) == 3

    def test_analyze_profile_with_structured_input(self):
        """Test analysis with structured profile input."""
        mock_llm = MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        structured = StudentProfileInput(
            name="Test Student",
            department="Computer Science",
            major="Data Science",
            skills=["Python", "SQL"],
            career_goal="Data Scientist"
        )
        
        result = agent.analyze_profile_structured("Test profile", structured_profile=structured)
        
        assert isinstance(result, ProfileAnalysisResult)

    def test_analyze_profile_empty_raises(self):
        """Test empty profile raises AgentError."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider())
        
        with pytest.raises(AgentError) as exc_info:
            agent.analyze_profile("")
        
        assert "cannot be empty" in str(exc_info.value)

    def test_analyze_profile_whitespace_raises(self):
        """Test whitespace-only profile raises AgentError."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider())
        
        with pytest.raises(AgentError):
            agent.analyze_profile("   \n\t  ")

    def test_process_request_returns_typed_response(self):
        """Test process_request returns ProfileSkillResponse."""
        mock_llm = MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        request = ProfileSkillRequest(student_profile="Test profile")
        response = agent.process_request(request)
        
        assert response.success is True
        assert response.agent == "ProfileSkillAgent"
        assert response.request_id is not None
        assert isinstance(response.result, ProfileAnalysisResult)

    def test_process_request_error_handling(self):
        """Test process_request handles errors gracefully."""
        # Mock LLM that returns invalid JSON
        mock_llm = MockLLMProvider(mock_response="Not valid JSON")
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        request = ProfileSkillRequest(student_profile="Test profile")
        response = agent.process_request(request)
        
        assert response.success is False
        assert response.agent == "ProfileSkillAgent"
        assert "error" in response.metadata

    def test_validate_input_empty_profile(self):
        """Test validate_input raises for empty profile."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider())
        request = ProfileSkillRequest(student_profile="")
        
        with pytest.raises(ValidationError) as exc_info:
            agent.validate_input(request)
        
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_input_valid_profile(self):
        """Test validate_input passes for valid profile."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider())
        request = ProfileSkillRequest(student_profile="Valid profile")
        
        # Should not raise
        agent.validate_input(request)

    def test_format_text_response(self):
        """Test _format_text_response produces expected format."""
        mock_llm = MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        # Create a minimal result
        result = ProfileAnalysisResult(
            student_summary="Test summary",
            identified_skills=[
                SkillAssessment(skill="Python", proficiency_level="intermediate", evidence="Listed", confidence=0.9)
            ],
            strong_skills=["Python"],
            weak_skills=[],
            missing_skills=[
                SkillGap(skill="Deep Learning", importance="critical", reason="Needed", current_level="none")
            ],
            recommended_skills=[
                RecommendedSkill(skill="Deep Learning", category="technical", priority="immediate", reason="Needed", estimated_weeks=8)
            ],
            learning_roadmap=[
                LearningRoadmapStep(step=1, title="Step 1", description="Desc", skills_covered=["Deep Learning"], estimated_weeks=8)
            ]
        )
        
        formatted = agent._format_text_response(result)
        
        assert "PROFILE & SKILL ANALYSIS" in formatted
        assert "Test summary" in formatted
        assert "Python" in formatted
        assert "Deep Learning" in formatted
        assert "Step 1" in formatted

    def test_extract_json_from_markdown(self):
        """Test _extract_json handles markdown code blocks."""
        mock_llm = MockLLMProvider(mock_response=MOCK_STRUCTURED_RESPONSE)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        # Test with markdown
        markdown_response = f"```json\n{MOCK_STRUCTURED_RESPONSE}\n```"
        extracted = agent._extract_json(markdown_response)
        assert extracted.strip() == MOCK_STRUCTURED_RESPONSE.strip()
        
        # Test without markdown
        extracted = agent._extract_json(MOCK_STRUCTURED_RESPONSE)
        assert extracted.strip() == MOCK_STRUCTURED_RESPONSE.strip()
        
        # Test with generic code block
        generic_response = f"```\n{MOCK_STRUCTURED_RESPONSE}\n```"
        extracted = agent._extract_json(generic_response)
        assert extracted.strip() == MOCK_STRUCTURED_RESPONSE.strip()

    def test_json_decode_error_handling(self):
        """Test handling of invalid JSON from LLM."""
        mock_llm = MockLLMProvider(mock_response="This is not JSON at all")
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        request = ProfileSkillRequest(student_profile="Test")
        response = agent.process_request(request)
        
        assert response.success is False
        assert "error" in response.metadata

    def test_validation_error_on_missing_required_fields(self):
        """Test handling when LLM response has minimal fields (uses defaults)."""
        # Pydantic uses default empty lists for missing array fields
        minimal_response = '{"student_summary": "Test"}'
        mock_llm = MockLLMProvider(mock_response=minimal_response)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        request = ProfileSkillRequest(student_profile="Test")
        response = agent.process_request(request)
        
        # Should succeed with defaults for missing fields
        assert response.success is True
        assert response.result is not None
        assert response.result.student_summary == "Test"
        assert response.result.identified_skills == []
        assert response.result.strong_skills == []


class TestProfileSkillSchemas:
    """Tests for Profile & Skill schemas."""

    def test_student_profile_input_creation(self):
        """Test StudentProfileInput can be created with all fields."""
        profile = StudentProfileInput(
            name="Test",
            department="CS",
            major="AI",
            cgpa=3.5,
            academic_year=3,
            skills=["Python", "ML"],
            interests=["NLP"],
            career_goal="ML Engineer",
            current_challenges=["Deep Learning"],
            preferred_learning_style="hands-on",
            time_availability_hours_per_week=10
        )
        
        assert profile.name == "Test"
        assert profile.cgpa == 3.5
        assert len(profile.skills) == 2

    def test_student_profile_input_validation(self):
        """Test StudentProfileInput validates CGPA range."""
        with pytest.raises(Exception):
            StudentProfileInput(cgpa=5.0)  # Invalid - max 4.0
        
        with pytest.raises(Exception):
            StudentProfileInput(cgpa=-1.0)  # Invalid - min 0.0

    def test_skill_assessment_creation(self):
        """Test SkillAssessment creation."""
        skill = SkillAssessment(
            skill="Python",
            proficiency_level="intermediate",
            evidence="Listed in profile",
            confidence=0.85
        )
        
        assert skill.skill == "Python"
        assert skill.proficiency_level == "intermediate"
        assert skill.confidence == 0.85

    def test_skill_gap_creation(self):
        """Test SkillGap creation."""
        gap = SkillGap(
            skill="Deep Learning",
            importance="critical",
            reason="Required for role",
            current_level="none"
        )
        
        assert gap.skill == "Deep Learning"
        assert gap.importance == "critical"
        assert gap.current_level == "none"

    def test_recommended_skill_creation(self):
        """Test RecommendedSkill creation."""
        rec = RecommendedSkill(
            skill="TypeScript",
            category="technical",
            priority="short_term",
            reason="Better type safety",
            suggested_resources=["TypeScript Handbook"],
            estimated_weeks=4
        )
        
        assert rec.skill == "TypeScript"
        assert rec.category == "technical"
        assert rec.priority == "short_term"
        assert rec.estimated_weeks == 4

    def test_learning_roadmap_step_creation(self):
        """Test LearningRoadmapStep creation."""
        step = LearningRoadmapStep(
            step=1,
            title="Learn TypeScript",
            description="Migrate from JavaScript",
            skills_covered=["TypeScript"],
            estimated_weeks=3,
            prerequisites=["JavaScript"],
            milestones=["Convert project", "Build typed components"]
        )
        
        assert step.step == 1
        assert step.title == "Learn TypeScript"
        assert step.estimated_weeks == 3
        assert len(step.prerequisites) == 1
        assert len(step.milestones) == 2

    def test_profile_analysis_result_creation(self):
        """Test ProfileAnalysisResult creation with all fields."""
        result = ProfileAnalysisResult(
            student_summary="Summary",
            identified_skills=[],
            strong_skills=[],
            weak_skills=[],
            missing_skills=[],
            recommended_skills=[],
            learning_roadmap=[],
            metadata={"version": "1.0"}
        )
        
        assert result.student_summary == "Summary"
        assert result.metadata["version"] == "1.0"

    def test_profile_skill_request_creation(self):
        """Test ProfileSkillRequest creation."""
        request = ProfileSkillRequest(
            student_profile="Test profile",
            force_refresh=True
        )
        
        assert request.student_profile == "Test profile"
        assert request.force_refresh is True

    def test_profile_skill_response_creation(self):
        """Test ProfileSkillResponse creation."""
        from AI.schemas.profile_skill import ProfileSkillResponse
        
        response = ProfileSkillResponse(
            success=True,
            agent="ProfileSkillAgent",
            request_id="req-123",
            processing_time_ms=150.0,
            result=ProfileAnalysisResult(student_summary="Test"),
            metadata={"type": "structured"}
        )
        
        assert response.success is True
        assert response.agent == "ProfileSkillAgent"
        assert response.result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])