from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.gamification.presentation.schemas import (
    LeagueSeason,
    MyLeaguePosition,
    PointsBalance,
    PointsHistoryResponse,
    RankingResponse,
    SeasonsResponse,
)

points_router = APIRouter(prefix="/points", tags=["gamification"])
leagues_router = APIRouter(prefix="/leagues", tags=["gamification"])

LEAGUE_TZ = ZoneInfo("America/New_York")


def _current_week_season() -> LeagueSeason:
    now_et = datetime.now(LEAGUE_TZ)
    iso_year, iso_week, iso_weekday = now_et.isocalendar()
    monday_et = now_et - timedelta(days=iso_weekday - 1)
    monday_et = monday_et.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday_end_et = monday_et + timedelta(days=6, hours=21)
    season_id = f"{iso_year}-W{iso_week:02d}"
    return LeagueSeason(
        season_id=season_id,
        name=f"Week {iso_week}, {iso_year}",
        timezone="America/New_York",
        starts_at=monday_et,
        ends_at=sunday_end_et,
        is_current=True,
    )


@points_router.get("/me", response_model=PointsBalance, summary="My points balance")
def get_my_points(user: CurrentUser = Depends(get_current_user)) -> PointsBalance:
    return PointsBalance(
        user_id=user.user_id,
        total_points=0,
        weekly_points=0,
        season_points=0,
    )


@points_router.get("/history", response_model=PointsHistoryResponse, summary="Points-earning history")
def get_points_history(
    cursor: str | None = None,
    limit: int = Query(30, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> PointsHistoryResponse:
    return PointsHistoryResponse(items=[])


@leagues_router.get(
    "/me",
    response_model=MyLeaguePosition,
    summary="My league standing for the current season (tier, rank, score, band)",
)
def get_my_league(user: CurrentUser = Depends(get_current_user)) -> MyLeaguePosition:
    season = _current_week_season()
    return MyLeaguePosition(
        season_id=season.season_id,
        tier="green",
        tier_label="Green League",
        group_id="grp_green_01",
        group_size=30,
        rank=None,
        band=None,
        season_points=0,
        last_activity_at=None,
        promote_cutoff_rank=6,
        demote_cutoff_rank=25,
        can_promote=True,
        can_demote=False,
        previous_tier=None,
        next_tier="lime",
    )


@leagues_router.get("/current", response_model=LeagueSeason, summary="Current weekly season")
def get_current_season() -> LeagueSeason:
    return _current_week_season()


@leagues_router.get(
    "/current/rankings",
    response_model=RankingResponse,
    summary="Live leaderboard of my current group",
)
def get_current_rankings(
    limit: int = Query(30, ge=1, le=30),
    user: CurrentUser = Depends(get_current_user),
) -> RankingResponse:
    season = _current_week_season()
    return RankingResponse(
        season_id=season.season_id,
        group_id="grp_green_01",
        updated_at=datetime.now(timezone.utc),
        entries=[],
        me=None,
    )


@leagues_router.get(
    "/current/groups/{group_id}/rankings",
    response_model=RankingResponse,
    summary="Live leaderboard of a specific group",
)
def get_current_group_rankings(
    group_id: str,
    limit: int = Query(30, ge=1, le=30),
    user: CurrentUser = Depends(get_current_user),
) -> RankingResponse:
    season = _current_week_season()
    return RankingResponse(
        season_id=season.season_id,
        group_id=group_id,
        updated_at=datetime.now(timezone.utc),
        entries=[],
    )


@leagues_router.get("/seasons", response_model=SeasonsResponse, summary="List past & current seasons")
def list_seasons() -> SeasonsResponse:
    return SeasonsResponse(items=[_current_week_season()])


@leagues_router.get(
    "/seasons/{season_id}/rankings",
    response_model=RankingResponse,
    summary="Frozen leaderboard of my group for a past season",
)
def get_season_rankings(
    season_id: str,
    limit: int = Query(30, ge=1, le=30),
    user: CurrentUser = Depends(get_current_user),
) -> RankingResponse:
    return RankingResponse(
        season_id=season_id,
        group_id="grp_green_01",
        updated_at=datetime.now(timezone.utc),
        entries=[],
    )
