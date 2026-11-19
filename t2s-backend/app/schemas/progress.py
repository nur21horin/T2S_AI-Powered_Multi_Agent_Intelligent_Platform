from uuid import UUID

from pydantic import BaseModel


class ProgressRead(BaseModel):
    user_id: UUID
    room_id: UUID | None = None
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    awaiting_review: int
    evaluated_tasks: int
    average_score: float | None
    total_earned_score: int
    total_possible_score: int
    completion_percentage: float
