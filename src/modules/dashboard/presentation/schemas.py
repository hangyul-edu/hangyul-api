from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DashboardGoal(BaseModel):
    key: Literal["daily_sentences", "daily_questions"] = Field(
        description="Goal identifier. Only count-based item goals exist; study time is not a goal."
    )
    label: str
    target: int = Field(description="Daily milestone count (5, 10, 20, 30, or 40).")
    current: int = Field(description="Count achieved today so far. May exceed `target`.")
    achieved: bool = Field(
        description="True once `current >= target` for the day; stays true even if `current` keeps growing."
    )
    track_id: Literal["trk_conversation", "trk_topik"] = Field(
        description="Which track the goal belongs to (sentences → trk_conversation, questions → trk_topik).",
    )


class DashboardTrack(BaseModel):
    track_id: str
    name: str
    level: int
    level_label: str
    progress_ratio: float = Field(ge=0.0, le=1.0)
    next_lesson_id: str | None = None


class DashboardSummary(BaseModel):
    user_id: str
    streak_days: int
    last_study_date: date | None = None
    today_minutes: int = Field(default=0, description="Display-only. Minutes studied today; not a goal target.")
    goals: list[DashboardGoal]
    tracks: list[DashboardTrack]
    paywall_required: bool = False
    ad_placement: Literal["none", "banner", "interstitial"] = "none"


class StreakResponse(BaseModel):
    current: int
    best: int
    freeze_tokens: int = 0
    last_study_date: date | None = None
