from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DailyGoalKey = Literal["daily_sentences", "daily_questions"]
DailyProgressTrackId = Literal["trk_conversation", "trk_topik"]


class DailyProgress(BaseModel):
    """Shared shape for the daily-goal state surfaced on session start and in attempt responses."""

    track_id: DailyProgressTrackId
    goal_key: DailyGoalKey = Field(
        description=(
            "Which goal this progress refers to. Conversation tracks `daily_sentences`, TOPIK "
            "tracks `daily_questions`."
        )
    )
    target: int = Field(description="Daily milestone: 5, 10, 20, 30, or 40.")
    current: int = Field(
        ge=0,
        description="Correctly completed items counted today so far. May exceed `target` (overflow still tracked).",
    )
    achieved: bool = Field(
        description="True once `current >= target` for the day. Latches — does not revert if current grows further.",
    )
    resets_at: datetime = Field(description="Start of the user's next local day, when the counter rolls over.")


class DailyProgressListResponse(BaseModel):
    items: list[DailyProgress]
