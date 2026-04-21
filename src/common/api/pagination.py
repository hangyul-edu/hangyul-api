from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(default=None, description="Opaque cursor for the next page; null when exhausted.")
    has_more: bool = False


class ProblemDetails(BaseModel):
    type: str = Field(default="about:blank", description="A URI reference that identifies the problem type.")
    title: str
    status: int
    code: str
    detail: str
    instance: str | None = None
