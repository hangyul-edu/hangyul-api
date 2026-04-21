from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

QuizType = Literal["multiple_choice", "fill_blank", "typing", "ordering", "listening"]


class QuizChoice(BaseModel):
    key: str
    text: str


class QuizQuestion(BaseModel):
    quiz_id: str
    type: QuizType
    prompt: str
    prompt_translation: str | None = None
    audio_url: str | None = None
    choices: list[QuizChoice] = Field(default_factory=list)
    hint: str | None = None
    level: int = Field(ge=1, le=10)


class QuizDailySetResponse(BaseModel):
    date: str = Field(description="YYYY-MM-DD")
    questions: list[QuizQuestion]


class QuizListResponse(BaseModel):
    items: list[QuizQuestion]
    total: int


class QuizAttemptRequest(BaseModel):
    answer: str = Field(description="Selected choice key, typed text, or ordered payload.")
    elapsed_ms: int = Field(ge=0)


class QuizAttemptResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    correct: bool
    correct_answer: str | None = None
    explanation: str | None = None
    xp_earned: int
    submitted_at: datetime


class QuizAttempt(BaseModel):
    attempt_id: str
    quiz_id: str
    correct: bool
    submitted_at: datetime


class QuizAttemptsResponse(BaseModel):
    items: list[QuizAttempt]
    total_attempts: int
    total_correct: int
