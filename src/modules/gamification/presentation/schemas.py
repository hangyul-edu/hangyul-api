from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

LeagueTier = Literal["green", "lime", "yellow", "orange"]


class PointsBalance(BaseModel):
    user_id: str
    total_points: int
    weekly_points: int
    season_points: int
    next_tier_points: int | None = None


class PointsEvent(BaseModel):
    event_id: str
    reason: str = Field(description="Human-readable explanation (quiz_correct, streak_bonus, ...)")
    amount: int
    occurred_at: datetime


class PointsHistoryResponse(BaseModel):
    items: list[PointsEvent]
    next_cursor: str | None = None


class MyLeaguePosition(BaseModel):
    tier: LeagueTier
    tier_label: str
    rank: int | None
    points: int
    promotion_threshold: int
    demotion_threshold: int
    next_tier: LeagueTier | None = None


class LeagueSeason(BaseModel):
    season_id: str
    name: str = Field(description="e.g. '2026 Spring Season'")
    starts_on: date
    ends_on: date
    is_current: bool = False


class SeasonsResponse(BaseModel):
    items: list[LeagueSeason]


class RankingEntry(BaseModel):
    rank: int
    user_id: str
    nickname: str
    avatar_url: str | None = None
    tier: LeagueTier
    points: int


class RankingResponse(BaseModel):
    season_id: str
    updated_at: datetime
    entries: list[RankingEntry]
    me: RankingEntry | None = None
