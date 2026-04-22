from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.modules.quizzes.presentation.schemas import QuizQuestion
from src.modules.sentences.presentation.schemas import Sentence


class RecommendationQuota(BaseModel):
    daily_limit: int | None = Field(
        description=(
            "Maximum AI-recommended items a user may receive per day. Null for premium / trial "
            "members (no limit). Non-subscribed members are capped at 5 per day across sentences "
            "and questions combined."
        ),
    )
    used_today: int = Field(ge=0, description="Items already granted to this user today.")
    remaining_today: int | None = Field(
        description=(
            "daily_limit - used_today. Null for unlimited quotas. When this reaches 0, further "
            "calls return 402 subscription_required with an upsell payload."
        ),
    )
    resets_at: datetime = Field(
        description="When the quota counter rolls over (start of the user's next local day).",
    )


class RecommendationRequestSchema(BaseModel):
    user_id: str
    situation: str
    grammar_focus: str
    mode: str = "fresh"
    previous_sentence: str | None = None


class RecommendationResponseSchema(BaseModel):
    sentence: str
    translation: str
    grammar_focus: str
    target_level: str
    explanation: str
    next_suggestions: list[str]


class SentenceRecommendationRequest(BaseModel):
    level: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description=(
            "Target difficulty (Conversation scale 1..10). Always applied. Defaults to the caller's "
            "Conversation current_level if omitted; should normally match the current level."
        ),
    )
    prompt: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Optional refinement typed by the user in the on-screen prompt input — e.g. "
            "'sentences I can use when ordering food'. Narrows topic/scenario WITHIN `level`; "
            "it does not override the level."
        ),
    )
    count: int = Field(default=5, ge=1, le=20)


class SentenceRecommendationResponse(BaseModel):
    track_id: Literal["trk_conversation"] = "trk_conversation"
    level: int
    prompt: str | None = None
    items: list[Sentence]
    quota: RecommendationQuota = Field(
        description="Caller's remaining AI-recommendation allowance after this response.",
    )


class QuestionRecommendationRequest(BaseModel):
    level: int | None = Field(
        default=None,
        ge=1,
        le=6,
        description=(
            "Target TOPIK 급수 (1..6). Always applied. Defaults to the caller's TOPIK current_level "
            "if omitted; should normally match the current level."
        ),
    )
    prompt: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Optional refinement typed by the user in the on-screen prompt input — e.g. "
            "'피동 grammar questions'. Narrows topic/scenario WITHIN `level`; it does not override "
            "the level."
        ),
    )
    count: int = Field(default=5, ge=1, le=20)


class QuestionRecommendationResponse(BaseModel):
    track_id: Literal["trk_topik"] = "trk_topik"
    level: int
    prompt: str | None = None
    items: list[QuizQuestion]
    quota: RecommendationQuota = Field(
        description="Caller's remaining AI-recommendation allowance after this response.",
    )


class RecommendationHistoryItem(BaseModel):
    item_id: str
    kind: Literal["sentences", "questions"]
    level: int
    prompt: str | None = None
    recommended_at: str = Field(description="ISO-8601 timestamp")


class RecommendationHistoryResponse(BaseModel):
    items: list[RecommendationHistoryItem]
    next_cursor: str | None = None
