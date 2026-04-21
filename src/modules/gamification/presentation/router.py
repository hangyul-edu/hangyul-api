from __future__ import annotations

from datetime import date, datetime, timezone

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


@points_router.get("/me", response_model=PointsBalance, summary="My points balance")
def get_my_points(user: CurrentUser = Depends(get_current_user)) -> PointsBalance:
    return PointsBalance(
        user_id=user.user_id,
        total_points=0,
        weekly_points=0,
        season_points=0,
        next_tier_points=100,
    )


@points_router.get("/history", response_model=PointsHistoryResponse, summary="Points-earning history")
def get_points_history(
    cursor: str | None = None,
    limit: int = Query(30, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> PointsHistoryResponse:
    return PointsHistoryResponse(items=[])


@leagues_router.get("/me", response_model=MyLeaguePosition, summary="My league standing")
def get_my_league(user: CurrentUser = Depends(get_current_user)) -> MyLeaguePosition:
    return MyLeaguePosition(
        tier="green",
        tier_label="Green League",
        rank=None,
        points=0,
        promotion_threshold=500,
        demotion_threshold=0,
        next_tier="lime",
    )


@leagues_router.get("/current", response_model=LeagueSeason, summary="Current league season")
def get_current_season() -> LeagueSeason:
    return LeagueSeason(
        season_id="2026-spring",
        name="2026 Spring Season",
        starts_on=date(2026, 3, 1),
        ends_on=date(2026, 5, 31),
        is_current=True,
    )


@leagues_router.get("/current/rankings", response_model=RankingResponse, summary="Current season leaderboard")
def get_current_rankings(
    limit: int = Query(50, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
) -> RankingResponse:
    return RankingResponse(season_id="2026-spring", updated_at=datetime.now(timezone.utc), entries=[])


@leagues_router.get("/seasons", response_model=SeasonsResponse, summary="List past & current seasons")
def list_seasons() -> SeasonsResponse:
    return SeasonsResponse(items=[])


@leagues_router.get(
    "/seasons/{season_id}/rankings",
    response_model=RankingResponse,
    summary="Rankings for a specific season",
)
def get_season_rankings(
    season_id: str,
    limit: int = Query(50, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
) -> RankingResponse:
    return RankingResponse(season_id=season_id, updated_at=datetime.now(timezone.utc), entries=[])
