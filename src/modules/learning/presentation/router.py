from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.learning.presentation.schemas import (
    CalendarResponse,
    EnrollResponse,
    Lecture,
    LectureProgressRequest,
    LectureProgressResponse,
    LectureVideoResponse,
    LecturesResponse,
    Level,
    LevelsResponse,
    StatsRange,
    StatsResponse,
    Track,
    TracksResponse,
)

tracks_router = APIRouter(prefix="/tracks", tags=["learning"])
learning_router = APIRouter(prefix="/learning", tags=["learning"])
lectures_router = APIRouter(prefix="/lectures", tags=["learning"])


@tracks_router.get("", response_model=TracksResponse, summary="List learning tracks")
def list_tracks(user: CurrentUser = Depends(get_current_user)) -> TracksResponse:
    return TracksResponse(
        items=[
            Track(track_id="trk_topik", kind="topik", name="TOPIK", total_levels=10, enrolled=True),
            Track(track_id="trk_conversation", kind="conversation", name="일상 회화", total_levels=12),
        ]
    )


@tracks_router.get("/{track_id}", response_model=Track, summary="Get track detail")
def get_track(track_id: str, user: CurrentUser = Depends(get_current_user)) -> Track:
    return Track(track_id=track_id, kind="topik", name="TOPIK", total_levels=10, enrolled=True)


@tracks_router.get("/{track_id}/levels", response_model=LevelsResponse, summary="List levels in a track")
def list_levels(track_id: str, user: CurrentUser = Depends(get_current_user)) -> LevelsResponse:
    items = [
        Level(track_id=track_id, level=i, label=f"학습 레벨 {i}", unlocked=i <= 1, total_lessons=10)
        for i in range(1, 11)
    ]
    return LevelsResponse(items=items)


@tracks_router.post(
    "/{track_id}/enroll",
    response_model=EnrollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll in a track",
)
def enroll_track(track_id: str, user: CurrentUser = Depends(get_current_user)) -> EnrollResponse:
    return EnrollResponse(track_id=track_id, enrolled=True, current_level=1)


@learning_router.get("/calendar", response_model=CalendarResponse, summary="Daily study calendar")
def get_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    user: CurrentUser = Depends(get_current_user),
) -> CalendarResponse:
    return CalendarResponse(from_date=from_date, to_date=to_date, days=[], studied_days=0)


@learning_router.get("/stats", response_model=StatsResponse, summary="Aggregated study stats")
def get_stats(
    range: StatsRange = Query("week"),
    user: CurrentUser = Depends(get_current_user),
) -> StatsResponse:
    return StatsResponse(range=range, total_minutes=0, total_sentences=0, total_xp=0, points=[])


@lectures_router.get("", response_model=LecturesResponse, summary="List lectures for a level")
def list_lectures(
    track_id: str = Query(...),
    level: int = Query(..., ge=1),
    user: CurrentUser = Depends(get_current_user),
) -> LecturesResponse:
    return LecturesResponse(items=[])


@lectures_router.get("/{lecture_id}", response_model=Lecture, summary="Get lecture detail")
def get_lecture(lecture_id: str, user: CurrentUser = Depends(get_current_user)) -> Lecture:
    return Lecture(
        lecture_id=lecture_id,
        track_id="trk_topik",
        level=1,
        title="인사 표현",
        kind="video",
        duration_seconds=180,
    )


@lectures_router.get(
    "/{lecture_id}/video",
    response_model=LectureVideoResponse,
    summary="Get signed video URL for a lecture",
)
def get_lecture_video(lecture_id: str, user: CurrentUser = Depends(get_current_user)) -> LectureVideoResponse:
    return LectureVideoResponse(
        lecture_id=lecture_id,
        video_url=f"https://cdn.example.com/lectures/{lecture_id}/hls.m3u8?token=...",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@lectures_router.post(
    "/{lecture_id}/progress",
    response_model=LectureProgressResponse,
    summary="Report playback progress",
)
def report_lecture_progress(
    lecture_id: str,
    payload: LectureProgressRequest,
    user: CurrentUser = Depends(get_current_user),
) -> LectureProgressResponse:
    return LectureProgressResponse(
        lecture_id=lecture_id,
        position_seconds=payload.position_seconds,
        completed=payload.completed,
        xp_earned=5 if payload.completed else 0,
    )
