from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.common.api.pagination import CursorPage

SentenceStatus = Literal["new", "learning", "mastered", "bookmarked"]


class SentenceExample(BaseModel):
    korean: str
    romanization: str | None = None
    translation: str
    audio_url: str | None = None


class Sentence(BaseModel):
    sentence_id: str
    korean: str
    romanization: str | None = None
    translation: str
    topic: str | None = None
    level: int = Field(ge=1, le=10)
    audio_url: str | None = None
    grammar_points: list[str] = Field(default_factory=list)
    examples: list[SentenceExample] = Field(default_factory=list)
    bookmarked: bool = False
    status: SentenceStatus = "new"
    last_studied_at: datetime | None = None


class SentencePage(CursorPage[Sentence]):
    pass


class BookmarkResponse(BaseModel):
    sentence_id: str
    bookmarked: bool


class ListenEventRequest(BaseModel):
    position_ms: int = 0
    completed: bool = False


class ListenEventResponse(BaseModel):
    sentence_id: str
    play_count: int


class AudioUrlResponse(BaseModel):
    sentence_id: str
    audio_url: str
    expires_at: datetime
