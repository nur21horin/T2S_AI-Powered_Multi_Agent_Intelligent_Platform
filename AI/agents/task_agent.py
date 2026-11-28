"""Task Agent for T2S platform."""
import json
import uuid
from typing import Any, Optional

from AI.agents.base import BaseAgent
from AI.exceptions import AgentError, ValidationError
from AI.prompts.task import (
    TASK_GENERATION_SYSTEM_PROMPT,
    TASK_GENERATION_USER_PROMPT,
    TASK_EVALUATION_SYSTEM_PROMPT,
    TASK_EVALUATION_USER_PROMPT,
    TASK_PROGRESS_SYSTEM_PROMPT,
    TASK_PROGRESS_USER_PROMPT,
)
from AI.schemas.task import (
    TaskAgentRequest,
    TaskAgentResponse,
    TaskGenerationInput,
    TaskGenerationResult,
    TaskSubmissionInput,
    TaskEvaluationResult,
    TaskProgressInput,
    TaskProgressResult,
    GeneratedTask,
    TaskEvaluationResult as TaskEvalResult,
)


class TaskAgent(BaseAgent):
    """Agent for generating, evaluating, and tracking learning tasks."""

    agent_name = "TaskAgent"
    agent_description = "Generates learning tasks, evaluates submissions, and tracks progress"

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

    def generate_tasks(
        self,
        skill_gaps: list[str],
        learning_goals: list[str],
        student_profile: str = "",
        difficulty: str = "beginner",
        task_count: int = 3,
        duration_weeks: Optional[int] = None,
        preferred_format: str = "mixed"
    ) -> TaskGenerationResult:
        """
        Generate learning tasks for skill gaps.
        
        Args:
            skill_gaps: List of skills to address
            learning_goals: Learning objectives
            student_profile: Student context
            difficulty: Task difficulty level
            task_count: Number of tasks to generate
            duration_weeks: Learning duration
            preferred_format: Preferred task format
            
        Returns:
            TaskGenerationResult with generated tasks
        """
        request = TaskAgentRequest(
            action="generate",
            generation_input=TaskGenerationInput(
                student_profile=student_profile,
                skill_gaps=skill_gaps,
                learning_goals=learning_goals,
                difficulty=difficulty,
                task_count=task_count,
                duration_weeks=duration_weeks,
                preferred_format=preferred_format
            )
        )
        response = self.process_request(request)
        
        if response.success and response.result:
            return response.result
        else:
            error_msg = response.metadata.get("error", "Unknown error")
            raise AgentError(f"Task generation failed: {error_msg}", agent_name=self.agent_name)

    def evaluate_submission(
        self,
        task_id: str,
        submission_content: str,
        task_description: str = "",
        acceptance_criteria: list[str] = None,
        submission_type: str = "text",
        student_id: Optional[str] = None,
        time_spent_hours: Optional[float] = None
    ) -> TaskEvaluationResult:
        """
        Evaluate a student's task submission.
        
        Args:
            task_id: Task identifier
            submission_content: Student's submission
            task_description: Task description for context
            acceptance_criteria: List of criteria to evaluate against
            submission_type: Type of submission
            student_id: Student identifier
            time_spent_hours: Time spent on task
            
        Returns:
            TaskEvaluationResult with score and feedback
        """
        request = TaskAgentRequest(
            action="evaluate",
            evaluation_input=TaskSubmissionInput(
                task_id=task_id,
                student_id=student_id,
                submission_content=submission_content,
                submission_type=submission_type,
                time_spent_hours=time_spent_hours
            )
        )
        # Store context for evaluation
        self._eval_context = {
            "task_description": task_description,
            "acceptance_criteria": acceptance_criteria or []
        }
        
        response = self.process_request(request)
        
        if response.success and response.result:
            return response.result
        else:
            error_msg = response.metadata.get("error", "Unknown error")
            raise AgentError(f"Evaluation failed: {error_msg}", agent_name=self.agent_name)

    def track_progress(
        self,
        student_id: str,
        task_ids: list[str] = None,
        include_completed: bool = True
    ) -> TaskProgressResult:
        """
        Track student's task progress.
        
        Args:
            student_id: Student identifier
            task_ids: Specific task IDs to check
            include_completed: Include completed tasks
            
        Returns:
            TaskProgressResult with progress analysis
        """
        request = TaskAgentRequest(
            action="progress",
            progress_input=TaskProgressInput(
                student_id=student_id,
                task_ids=task_ids or [],
                include_completed=include_completed
            )
        )
        response = self.process_request(request)
        
        if response.success and response.result:
            return response.result
        else:
            error_msg = response.metadata.get("error", "Unknown error")
            raise AgentError(f"Progress tracking failed: {error_msg}", agent_name=self.agent_name)

    def _process(self, request: TaskAgentRequest) -> Any:
        """Process structured request based on action."""
        if request.action == "generate":
            return self._generate_tasks(request.generation_input)
        elif request.action == "evaluate":
            return self._evaluate_submission(request.evaluation_input)
        elif request.action == "progress":
            return self._track_progress(request.progress_input)
        else:
            raise ValidationError(f"Unknown action: {request.action}", field="action")

    def _generate_tasks(self, input_data: TaskGenerationInput) -> TaskGenerationResult:
        """Generate tasks using LLM."""
        # Build user prompt
        skill_gaps_str = "\n".join(f"- {s}" for s in input_data.skill_gaps) or "None specified"
        learning_goals_str = "\n".join(f"- {g}" for g in input_data.learning_goals) or "None specified"
        student_profile = input_data.student_profile or "Not provided"
        duration = str(input_data.duration_weeks) if input_data.duration_weeks else "Not specified"
        
        user_prompt = TASK_GENERATION_USER_PROMPT.format(
            task_count=input_data.task_count,
            student_profile=student_profile,
            skill_gaps=skill_gaps_str,
            learning_goals=learning_goals_str,
            difficulty=input_data.difficulty,
            preferred_format=input_data.preferred_format,
            duration_weeks=duration
        )
        
        # Invoke LLM
        try:
            raw_response = self.invoke(
                user_input=user_prompt,
                system_prompt=TASK_GENERATION_SYSTEM_PROMPT
            )
        except Exception as e:
            raise AgentError(f"LLM invocation failed: {str(e)}", agent_name=self.agent_name) from e
        
        # Parse JSON response
        try:
            json_str = self._extract_json(raw_response)
            parsed = json.loads(json_str)
            result = TaskGenerationResult.model_validate(parsed)
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

    def _evaluate_submission(self, input_data: TaskSubmissionInput) -> TaskEvaluationResult:
        """Evaluate submission using LLM."""
        # Get context from process_request
        context = getattr(self, '_eval_context', {})
        task_description = context.get("task_description", "Not provided")
        acceptance_criteria = context.get("acceptance_criteria", [])
        
        criteria_str = "\n".join(f"- {c}" for c in acceptance_criteria) or "None provided"
        time_spent = f"{input_data.time_spent_hours} hours" if input_data.time_spent_hours else "Not specified"
        
        user_prompt = TASK_EVALUATION_USER_PROMPT.format(
            task_id=input_data.task_id,
            task_description=task_description,
            acceptance_criteria=criteria_str,
            submission_type=input_data.submission_type,
            submission_content=input_data.submission_content[:3000],  # Limit length
            time_spent_hours=time_spent
        )
        
        # Invoke LLM
        try:
            raw_response = self.invoke(
                user_input=user_prompt,
                system_prompt=TASK_EVALUATION_SYSTEM_PROMPT
            )
        except Exception as e:
            raise AgentError(f"LLM invocation failed: {str(e)}", agent_name=self.agent_name) from e
        
        # Parse JSON response
        try:
            json_str = self._extract_json(raw_response)
            parsed = json.loads(json_str)
            result = TaskEvaluationResult.model_validate(parsed)
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

    def _track_progress(self, input_data: TaskProgressInput) -> TaskProgressResult:
        """Track progress using LLM."""
        # In a real implementation, this would query a database
        # For now, we use LLM to analyze provided task data
        tasks_data = "No task data provided (would come from database in production)"
        
        user_prompt = TASK_PROGRESS_USER_PROMPT.format(
            student_id=input_data.student_id,
            tasks_data=tasks_data,
            completed_task_ids=", ".join([]),
            in_progress_task_ids=", ".join([])
        )
        
        # Invoke LLM
        try:
            raw_response = self.invoke(
                user_input=user_prompt,
                system_prompt=TASK_PROGRESS_SYSTEM_PROMPT
            )
        except Exception as e:
            raise AgentError(f"LLM invocation failed: {str(e)}", agent_name=self.agent_name) from e
        
        # Parse JSON response
        try:
            json_str = self._extract_json(raw_response)
            parsed = json.loads(json_str)
            result = TaskProgressResult.model_validate(parsed)
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
        
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()

    def process_request(self, request: TaskAgentRequest) -> TaskAgentResponse:
        """Process request and return typed response."""
        request_id = str(uuid.uuid4())
        
        try:
            result = self._process(request)
            
            return TaskAgentResponse(
                success=True,
                agent=self.agent_name,
                request_id=request_id,
                result=result,
                metadata={"action": request.action}
            )
        except Exception as e:
            return TaskAgentResponse(
                success=False,
                agent=self.agent_name,
                request_id=request_id,
                result=None,
                metadata={"error": str(e), "error_type": type(e).__name__, "action": request.action}
            )

    def validate_input(self, request: TaskAgentRequest) -> None:
        """Validate request input."""
        if request.action == "generate" and not request.generation_input:
            raise ValidationError("Generation input required for generate action", field="generation_input")
        if request.action == "evaluate" and not request.evaluation_input:
            raise ValidationError("Evaluation input required for evaluate action", field="evaluation_input")
        if request.action == "progress" and not request.progress_input:
            raise ValidationError("Progress input required for progress action", field="progress_input")


def create_task_agent(**kwargs) -> TaskAgent:
    """Factory function for creating TaskAgent."""
    return TaskAgent(**kwargs)