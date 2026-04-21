from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DashboardGoal(BaseModel):
    key: Literal["daily_minutes", "daily_sentences", "weekly_lessons"]
    label: str
    target: int
    current: int
    unit: Literal["minutes", "count"] = "count"


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
    today_minutes: int = 0
    today_minutes_goal: int
    goals: list[DashboardGoal]
    tracks: list[DashboardTrack]
    paywall_required: bool = False
    ad_placement: Literal["none", "banner", "interstitial"] = "none"


class StreakResponse(BaseModel):
    current: int
    best: int
    freeze_tokens: int = 0
    last_study_date: date | None = None
