from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

LeagueTier = Literal["green", "lime", "yellow", "orange", "golden"]

PointsReason = Literal[
    "attendance",
    "attendance_streak_bonus",
    "sentence_complete",
    "lecture_complete",
    "saved_sentence_review",
]

SeasonOutcome = Literal["promote", "maintain", "demote"]


class PointsBalance(BaseModel):
    user_id: str
    total_points: int
    weekly_points: int
    season_points: int


class PointsEvent(BaseModel):
    event_id: str
    reason: PointsReason
    amount: int
    occurred_at: datetime


class PointsHistoryResponse(BaseModel):
    items: list[PointsEvent]
    next_cursor: str | None = None


class MyLeaguePosition(BaseModel):
    season_id: str = Field(description="ISO-week label of the season this snapshot belongs to — e.g. '2026-W17'.")
    tier: LeagueTier
    tier_label: str

    # Group + position within the group ------------------------------------------
    group_id: str
    group_size: int = 30
    rank: int | None = Field(
        default=None,
        ge=1,
        le=30,
        description=(
            "My current rank inside the group (1 = first). Null until the first ranked event of "
            "the season has been recorded."
        ),
    )
    band: Literal["promote", "maintain", "demote"] | None = Field(
        default=None,
        description=(
            "Where my rank falls today: 'promote' (ranks 1..promote_cutoff_rank), 'maintain' "
            "(middle 60%), 'demote' (bottom 20%). Null while rank is null."
        ),
    )

    # Score ---------------------------------------------------------------------
    season_points: int = Field(
        ge=0,
        description="My accumulated season score (the value the leaderboard is sorted by, desc).",
    )
    last_activity_at: datetime | None = Field(
        default=None,
        description="Tie-break timestamp — when two entries share season_points, the later activity ranks higher.",
    )

    # Cutoffs + mobility --------------------------------------------------------
    promote_cutoff_rank: int = Field(default=6, description="Ranks 1–6 promote (top 20%).")
    demote_cutoff_rank: int = Field(default=25, description="Ranks 25–30 demote (bottom 20%).")
    can_promote: bool = True
    can_demote: bool = True
    previous_tier: LeagueTier | None = None
    next_tier: LeagueTier | None = None


class LeagueSeason(BaseModel):
    season_id: str = Field(
        description="ISO-week label computed in America/New_York (US Eastern), e.g. '2026-W17'."
    )
    name: str
    timezone: str = Field(
        default="America/New_York",
        description="Reference timezone for season boundaries. Handles EST/EDT automatically.",
    )
    starts_at: datetime = Field(
        description="Monday 00:00 ET (America/New_York) of the season week.",
    )
    ends_at: datetime = Field(
        description="Sunday 21:00 ET (America/New_York) of the season week.",
    )
    is_current: bool = False


class SeasonsResponse(BaseModel):
    items: list[LeagueSeason]


class RankingEntry(BaseModel):
    rank: int = Field(ge=1, le=30)
    user_id: str
    nickname: str
    avatar_url: str | None = None
    tier: LeagueTier
    group_id: str
    points: int
    last_activity_at: datetime | None = None
    outcome: SeasonOutcome | None = Field(
        default=None,
        description="Promote / maintain / demote; populated once the season has closed.",
    )


class RankingResponse(BaseModel):
    season_id: str
    group_id: str
    updated_at: datetime
    entries: list[RankingEntry]
    me: RankingEntry | None = None
