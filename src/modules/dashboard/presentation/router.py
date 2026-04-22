from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from src.common.api.progress import (
    DailyProgress,
    DailyProgressListResponse,
    DailyProgressTrackId,
)
from src.common.security.auth import CurrentUser, get_current_user
from src.modules.dashboard.presentation.schemas import (
    DashboardGoal,
    DashboardSummary,
    DashboardTrack,
    StreakResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _next_local_midnight() -> datetime:
    # Stub — real impl uses the user's timezone.
    return (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _stub_progress(track_id: DailyProgressTrackId) -> DailyProgress:
    return DailyProgress(
        track_id=track_id,
        goal_key="daily_sentences" if track_id == "trk_conversation" else "daily_questions",
        target=10,
        current=0,
        achieved=False,
        resets_at=_next_local_midnight(),
    )


@router.get("/summary", response_model=DashboardSummary, summary="Home dashboard snapshot")
def get_summary(user: CurrentUser = Depends(get_current_user)) -> DashboardSummary:
    return DashboardSummary(
        user_id=user.user_id,
        streak_days=0,
        last_study_date=None,
        today_minutes=0,
        goals=[
            DashboardGoal(
                key="daily_sentences",
                label="회화 문장",
                target=10,
                current=0,
                achieved=False,
                track_id="trk_conversation",
            ),
            DashboardGoal(
                key="daily_questions",
                label="TOPIK 문제",
                target=10,
                current=0,
                achieved=False,
                track_id="trk_topik",
            ),
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


@router.get(
    "/daily-progress",
    response_model=DailyProgressListResponse,
    summary="Today's daily-goal progress per track (called on 'Start Now' and on the home screen)",
    description=(
        "Focused snapshot of the user's daily-goal state. Returns one DailyProgress entry per "
        "applicable track; use `track_id` to scope to a single track on session start. The home "
        "screen calls this endpoint (or the larger /dashboard/summary) to render target / current / "
        "achieved counts alongside the streak and today's study time."
    ),
)
def get_daily_progress(
    track_id: DailyProgressTrackId | None = Query(
        default=None,
        description="Optional — returns just this track's progress when set.",
    ),
    user: CurrentUser = Depends(get_current_user),
) -> DailyProgressListResponse:
    all_tracks: list[DailyProgressTrackId] = ["trk_conversation", "trk_topik"]
    chosen = [track_id] if track_id else all_tracks
    return DailyProgressListResponse(items=[_stub_progress(t) for t in chosen])
