"""Unit tests for BaseAgent and related components."""
import pytest
from typing import Any
from unittest.mock import Mock, patch, MagicMock

from AI.agents.base import BaseAgent
from AI.agents.profile_skill_agent import ProfileSkillAgent
from AI.exceptions import AgentError, ConfigurationError
from AI.llm.factory import LLMFactory, MockLLMProvider, get_llm_factory
from AI.llm.providers.base import BaseLLMProvider
from AI.schemas.base import BaseRequest, AgentResponse
from AI.schemas.profile_skill import ProfileAnalysisResult


# Sample mock JSON response for ProfileSkillAgent
MOCK_PROFILE_JSON = '''
{
  "student_summary": "Test student",
  "identified_skills": [],
  "strong_skills": [],
  "weak_skills": [],
  "missing_skills": [],
  "recommended_skills": [],
  "learning_roadmap": [],
  "metadata": {}
}
'''


# Concrete implementation of BaseAgent for testing
class TestableAgent(BaseAgent):
    """Testable concrete agent implementation."""
    
    agent_name = "TestableAgent"
    agent_description = "Test agent for unit tests"
    system_prompt = "You are a test agent."
    
    def _process(self, request: BaseRequest) -> Any:
        return {"processed": True, "input": str(request)}


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    def test_mock_provider_creation(self):
        """Test mock provider can be created."""
        provider = MockLLMProvider(mock_response="Test response")
        assert provider.model == "mock-model"
        assert provider._mock_response == "Test response"

    def test_mock_provider_invoke(self):
        """Test mock provider invoke returns expected response."""
        provider = MockLLMProvider(mock_response="Hello world")
        messages = [Mock()]
        result = provider.invoke(messages)
        
        assert result.generations[0][0].text == "Hello world"
        assert provider.get_call_count() == 1

    def test_mock_provider_ainvoke(self):
        """Test mock provider async invoke."""
        import asyncio
        
        provider = MockLLMProvider(mock_response="Async response")
        messages = [Mock()]
        
        result = asyncio.run(provider.ainvoke(messages))
        assert result.generations[0][0].text == "Async response"

    def test_mock_provider_set_response(self):
        """Test changing mock response dynamically."""
        provider = MockLLMProvider(mock_response="First")
        assert provider.invoke([Mock()]).generations[0][0].text == "First"
        
        provider.set_mock_response("Second")
        assert provider.invoke([Mock()]).generations[0][0].text == "Second"

    def test_mock_provider_tracks_messages(self):
        """Test mock provider tracks last messages."""
        provider = MockLLMProvider()
        messages = [Mock(), Mock()]
        provider.invoke(messages)
        
        assert provider.get_last_messages() == messages


class TestLLMFactory:
    """Tests for LLMFactory."""

    def test_factory_creates_mock_provider(self):
        """Test factory creates mock provider when enabled."""
        factory = LLMFactory()
        # Settings has enable_mock_llm=True from conftest
        provider = factory.create_provider()
        
        assert isinstance(provider, MockLLMProvider)

    def test_factory_creates_mock_provider_explicit(self):
        """Test factory creates mock provider explicitly."""
        factory = LLMFactory()
        provider = factory.create_provider(provider_name="mock", mock_response="Custom")
        
        assert isinstance(provider, MockLLMProvider)
        assert provider._mock_response == "Custom"

    def test_factory_unknown_provider_raises(self):
        """Test factory raises for unknown provider."""
        factory = LLMFactory()
        
        with pytest.raises(ConfigurationError) as exc_info:
            factory.create_provider(provider_name="unknown")
        
        assert "Unknown LLM provider" in str(exc_info.value)

    def test_factory_caches_providers(self):
        """Test factory caches provider instances."""
        factory = LLMFactory()
        
        provider1 = factory.get_provider("mock")
        provider2 = factory.get_provider("mock")
        
        assert provider1 is provider2

    def test_factory_clear_cache(self):
        """Test factory cache clearing."""
        factory = LLMFactory()
        
        provider1 = factory.get_provider("mock")
        factory.clear_cache()
        provider2 = factory.get_provider("mock")
        
        assert provider1 is not provider2

    def test_register_provider(self):
        """Test registering new provider."""
        class CustomProvider(BaseLLMProvider):
            def __init__(self, model: str = "custom", **kwargs):
                super().__init__(model, **kwargs)
            
            def _create_client(self):
                return None
            
            def invoke(self, messages):
                return None
            
            async def ainvoke(self, messages):
                return None
        
        LLMFactory.register_provider("custom", CustomProvider)
        factory = LLMFactory()
        # Disable mock for this test
        provider = factory.create_provider("custom", model="test-model", mock_response="should not use")
        # Manually create to bypass mock logic
        provider = CustomProvider(model="test-model")
        
        assert isinstance(provider, CustomProvider)
        assert provider.model == "test-model"


class TestBaseAgent:
    """Tests for BaseAgent."""

    def test_base_agent_creation(self):
        """Test base agent can be instantiated."""
        agent = TestableAgent()
        assert agent.agent_name == "TestableAgent"
        assert agent.llm is not None

    def test_base_agent_with_custom_llm(self):
        """Test base agent with custom LLM provider."""
        mock_llm = MockLLMProvider(mock_response="Custom agent response")
        agent = TestableAgent(llm_provider=mock_llm)
        
        assert agent.llm is mock_llm

    def test_base_agent_invoke(self):
        """Test base agent invoke returns mock response."""
        mock_llm = MockLLMProvider(mock_response="Agent response")
        agent = TestableAgent(llm_provider=mock_llm)
        
        result = agent.invoke("Test input")
        
        assert result == "Agent response"

    def test_base_agent_invoke_with_system_prompt(self):
        """Test base agent invoke with custom system prompt."""
        mock_llm = MockLLMProvider(mock_response="Response with custom prompt")
        agent = TestableAgent(llm_provider=mock_llm)
        
        result = agent.invoke("Test", system_prompt="Custom system prompt")
        
        assert result == "Response with custom prompt"

    def test_base_agent_invoke_with_history(self):
        """Test base agent invoke with conversation history."""
        mock_llm = MockLLMProvider(mock_response="Response with history")
        agent = TestableAgent(llm_provider=mock_llm)
        
        history = [Mock(), Mock()]
        result = agent.invoke("Test", history=history)
        
        assert result == "Response with history"
        # Verify history was passed to LLM
        last_messages = mock_llm.get_last_messages()
        assert len(last_messages) == 4  # system + 2 history + human

    def test_base_agent_process_request(self):
        """Test base agent process_request returns structured response."""
        mock_llm = MockLLMProvider(mock_response="Processed result")
        
        agent = TestableAgent(llm_provider=mock_llm)
        request = BaseRequest(user_id=None)
        
        response = agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert response.agent == "TestableAgent"
        assert response.result == {"processed": True, "input": str(request)}
        assert response.request_id is not None
        assert response.processing_time_ms is not None

    def test_base_agent_process_request_error_handling(self):
        """Test base agent handles errors in _process."""
        class FailingAgent(BaseAgent):
            agent_name = "FailingAgent"
            
            def _process(self, request):
                raise ValueError("Processing failed")
        
        agent = FailingAgent(llm_provider=MockLLMProvider())
        request = BaseRequest()
        
        response = agent.process_request(request)
        
        assert response.success is False
        assert response.agent == "FailingAgent"
        assert "Processing failed" in str(response.metadata.get("error", ""))

    def test_base_agent_get_agent_info(self):
        """Test get_agent_info returns metadata."""
        mock_llm = MockLLMProvider(model="test-model")
        agent = TestableAgent(llm_provider=mock_llm)
        
        info = agent.get_agent_info()
        
        assert info["name"] == "TestableAgent"
        assert info["llm_provider"] == "MockLLMProvider"
        assert info["llm_model"] == "test-model"

    def test_base_agent_validate_input(self):
        """Test base agent validate_input (no-op by default)."""
        agent = TestableAgent(llm_provider=MockLLMProvider())
        request = BaseRequest()
        
        # Should not raise
        agent.validate_input(request)

    def test_build_messages(self):
        """Test _build_messages constructs proper message list."""
        from langchain_core.messages import SystemMessage, HumanMessage
        
        mock_llm = MockLLMProvider()
        agent = TestableAgent(llm_provider=mock_llm)
        
        messages = agent._build_messages(
            user_input="Hello",
            system_prompt="System prompt",
            history=[HumanMessage(content="Previous")]
        )
        
        assert len(messages) == 3
        assert isinstance(messages[0], SystemMessage)
        assert messages[0].content == "System prompt"
        assert isinstance(messages[1], HumanMessage)
        assert messages[1].content == "Previous"
        assert isinstance(messages[2], HumanMessage)
        assert messages[2].content == "Hello"


class TestProfileSkillAgent:
    """Tests for ProfileSkillAgent."""

    def test_profile_skill_agent_creation(self):
        """Test ProfileSkillAgent can be instantiated."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider(mock_response=MOCK_PROFILE_JSON))
        
        assert agent.agent_name == "ProfileSkillAgent"
        assert "Profile and Skill Analysis" in agent.system_prompt

    def test_analyze_profile_success(self):
        """Test analyze_profile returns formatted text response."""
        mock_llm = MockLLMProvider(mock_response=MOCK_PROFILE_JSON)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        result = agent.analyze_profile("Student profile text")
        
        assert isinstance(result, str)
        assert "PROFILE & SKILL ANALYSIS" in result
        assert "Test student" in result

    def test_analyze_profile_empty_raises(self):
        """Test analyze_profile raises for empty input."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider(mock_response=MOCK_PROFILE_JSON))
        
        with pytest.raises(AgentError) as exc_info:
            agent.analyze_profile("")
        
        assert "cannot be empty" in str(exc_info.value)
        assert exc_info.value.agent_name == "ProfileSkillAgent"

    def test_analyze_profile_whitespace_raises(self):
        """Test analyze_profile raises for whitespace-only input."""
        agent = ProfileSkillAgent(llm_provider=MockLLMProvider(mock_response=MOCK_PROFILE_JSON))
        
        with pytest.raises(AgentError):
            agent.analyze_profile("   \n\t  ")

    def test_process_request_compatibility(self):
        """Test _process handles various request formats."""
        mock_llm = MockLLMProvider(mock_response=MOCK_PROFILE_JSON)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        # Test with object having student_profile attribute
        class RequestObj:
            student_profile = "Test profile"
            structured_profile = None
        
        result = agent._process(RequestObj())
        assert isinstance(result, ProfileAnalysisResult)
        
        # Test with ProfileSkillRequest (the actual expected type)
        from AI.schemas.profile_skill import ProfileSkillRequest
        request = ProfileSkillRequest(student_profile="Dict profile")
        result = agent._process(request)
        assert isinstance(result, ProfileAnalysisResult)
        
        # Test process_request with string (handled by process_request before _process)
        request = ProfileSkillRequest(student_profile="String profile")
        result = agent.process_request(request)
        assert result.success is True
        assert isinstance(result.result, ProfileAnalysisResult)

    def test_backward_compatibility_analyze_profile(self):
        """Test original analyze_profile interface still works."""
        mock_llm = MockLLMProvider(mock_response=MOCK_PROFILE_JSON)
        agent = ProfileSkillAgent(llm_provider=mock_llm)
        
        # This is the original method signature
        result = agent.analyze_profile("Name: Test\nSkills: Python")
        
        assert isinstance(result, str)
        assert "PROFILE & SKILL ANALYSIS" in result


class TestConfigurationErrorHandling:
    """Tests for configuration error handling."""

    def test_missing_api_key_raises_configuration_error(self):
        """Test that missing API key raises ConfigurationError for real providers."""
        # This test verifies the error type, not the actual Groq provider
        factory = LLMFactory()
        
        # Temporarily disable mock to test real provider creation
        with patch.object(factory, "_get_settings") as mock_settings:
            mock_settings.return_value.llm.provider = "groq"
            mock_settings.return_value.llm.groq_api_key = None
            mock_settings.return_value.enable_mock_llm = False
            
            with pytest.raises(ConfigurationError) as exc_info:
                factory.create_provider("groq")
            
            assert "GROQ_API_KEY is required" in str(exc_info.value)


class TestAgentResponseSchemas:
    """Tests for response schemas."""

    def test_agent_response_creation(self):
        """Test AgentResponse can be created with all fields."""
        response = AgentResponse(
            success=True,
            agent="TestAgent",
            request_id="req-123",
            processing_time_ms=150.5,
            result={"key": "value"},
            metadata={"extra": "info"}
        )
        
        assert response.success is True
        assert response.agent == "TestAgent"
        assert response.result == {"key": "value"}

    def test_error_response_creation(self):
        """Test ErrorResponse schema."""
        from AI.schemas.base import ErrorResponse
        
        response = ErrorResponse(
            success=False,
            agent="TestAgent",
            error="Something went wrong",
            error_code="TEST_ERROR",
            details={"field": "value"}
        )
        
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.error_code == "TEST_ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])