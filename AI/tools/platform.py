"""Allowlisted, application-controlled interface to authorized platform tools."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlatformTool:
    name: str
    description: str
    arguments_schema: dict[str, Any]


TOOL_DESCRIPTIONS: dict[str, str] = {
    "get_student_profile": "Read the authenticated user's own profile.",
    "get_student_skills": "Read the authenticated user's skills and interests.",
    "get_student_progress": "Read the authenticated user's personal task progress.",
    "get_available_tasks": "List published tasks in rooms the user may view.",
    "get_assigned_tasks": "List published tasks in the user's active rooms.",
    "search_matching_tasks": "Search visible published tasks by text.",
    "search_student_profiles": "Find opted-in students using discoverable skill and department data.",
    "get_project_requirements": "Read requirements for a project visible to the user.",
    "find_complementary_skills": "Find opted-in students whose skills match requested skills.",
    "get_available_opportunities": "List published opportunities only.",
    "search_matching_opportunities": "Search published opportunity records by text.",
    "search_research_opportunities": "Search published research opportunities.",
    "get_research_projects": "List published research opportunities.",
    "retrieve_knowledge_resources": "Retrieve resources if resource records are available.",
    "semantic_search_resources": "Semantic search is unavailable until resources and a vector index exist.",
}
PLATFORM_TOOL_NAMES = frozenset(TOOL_DESCRIPTIONS)


class PlatformToolExecutor:
    """Execute only the registered tool names on a request-scoped backend service.

    The service is expected to be created by the backend's authenticated dependency.
    Python cannot prevent trusted application code from constructing objects directly;
    this adapter rejects objects that do not implement the backend tool contract.
    """

    __slots__ = ("__service",)

    def __init__(self, tool_service: Any) -> None:
        if not callable(getattr(tool_service, "execute_tool", None)) or not callable(
            getattr(tool_service, "input_model_for", None)
        ):
            raise TypeError("PlatformToolExecutor requires a validated backend tool service.")
        if not hasattr(tool_service, "actor") or not hasattr(tool_service, "db"):
            raise TypeError("PlatformToolExecutor requires an identity-bound backend tool service.")
        self.__service = tool_service

    @property
    def definitions(self) -> list[PlatformTool]:
        definitions = []
        for name, description in TOOL_DESCRIPTIONS.items():
            model = self.__service.input_model_for(name)
            definitions.append(PlatformTool(name, description, model.model_json_schema()))
        return definitions

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in PLATFORM_TOOL_NAMES:
            return {
                "success": False,
                "data": None,
                "error": {"code": "unknown_tool", "message": "The requested tool is not available."},
                "explanation": None,
            }
        return self.__service.execute_tool(name, arguments)
