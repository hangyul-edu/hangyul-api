from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SubmissionStatus = Literal["pending", "graded", "failed"]


class WritingPrompt(BaseModel):
    prompt_id: str
    topic: str
    level: int = Field(ge=1, le=10)
    instruction: str
    reference_sentence: str | None = None
    min_length: int = 20
    max_length: int = 500


class WritingPromptsResponse(BaseModel):
    items: list[WritingPrompt]


class WritingSubmissionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class WritingFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    grammar_issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    corrected_text: str | None = None


class WritingSubmission(BaseModel):
    submission_id: str
    prompt_id: str
    text: str
    status: SubmissionStatus
    submitted_at: datetime
    feedback: WritingFeedback | None = None


class WritingSubmissionsResponse(BaseModel):
    items: list[WritingSubmission]
