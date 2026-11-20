from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import EvaluationStatus


class EvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: int = Field(ge=0, le=100000)
    feedback: str | None = Field(default=None, max_length=20000)
    status: EvaluationStatus = EvaluationStatus.FINALIZED


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    submission_id: UUID
    evaluator_id: UUID
    score: int
    feedback: str | None
    status: EvaluationStatus
    evaluated_at: datetime
    created_at: datetime
    updated_at: datetime
