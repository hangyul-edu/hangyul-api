from __future__ import annotations

from fastapi import APIRouter, Depends

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.dashboard.presentation.schemas import (
    DashboardGoal,
    DashboardSummary,
    DashboardTrack,
    StreakResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Home dashboard snapshot")
def get_summary(user: CurrentUser = Depends(get_current_user)) -> DashboardSummary:
    return DashboardSummary(
        user_id=user.user_id,
        streak_days=0,
        last_study_date=None,
        today_minutes=0,
        today_minutes_goal=10,
        goals=[
            DashboardGoal(key="daily_minutes", label="오늘 목표 시간", target=10, current=0, unit="minutes"),
            DashboardGoal(key="daily_sentences", label="오늘 목표 문장", target=10, current=0),
        ],
        tracks=[
            DashboardTrack(
                track_id="trk_topik",
                name="TOPIK",
                level=1,
                level_label="학습 레벨 1",
                progress_ratio=0.0,
                next_lesson_id=None,
            )
        ],
        paywall_required=False,
    )


@router.get("/streak", response_model=StreakResponse, summary="Current and best streak")
def get_streak(user: CurrentUser = Depends(get_current_user)) -> StreakResponse:
    return StreakResponse(current=0, best=0, freeze_tokens=0)
