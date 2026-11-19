from fastapi import Query
from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def pagination_params(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Pagination:
    return Pagination(page=page, limit=limit)
