from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from src.common.exceptions import NotFoundError
from src.common.security.auth import CurrentUser, get_current_user
from src.modules.learning.presentation.schemas import (
    CalendarResponse,
    Lecture,
    LectureProgressRequest,
    LectureProgressResponse,
    LectureVideoResponse,
    LecturesResponse,
    Level,
    LevelsResponse,
    MyLearningState,
    MyProgressionState,
    ProgressionInfo,
    ProgressionKind,
    StatsRange,
    StatsResponse,
    Track,
    TracksResponse,
    UpdateCurrentLevelRequest,
    UpdateTopikTargetRequest,
)

tracks_router = APIRouter(prefix="/tracks", tags=["learning"])
learning_router = APIRouter(prefix="/learning", tags=["learning"])
lectures_router = APIRouter(prefix="/lectures", tags=["learning"])
me_learning_router = APIRouter(prefix="/me/learning", tags=["learning"])

_DEFAULT_PROGRESSIONS: list[ProgressionInfo] = [
    ProgressionInfo(kind="lectures", total_levels=10),
    ProgressionInfo(kind="sentences", total_levels=10),
]

_TRACK_CATALOG: dict[str, Track] = {
    "trk_topik": Track(
        track_id="trk_topik",
        kind="topik",
        name="TOPIK",
        description="TOPIK 급수 대비 트랙. 강의와 문장 학습이 독립적으로 진행됩니다.",
        progressions=_DEFAULT_PROGRESSIONS,
    ),
    "trk_conversation": Track(
        track_id="trk_conversation",
        kind="conversation",
        name="회화",
        description="일상 회화 중심 트랙. 강의와 문장 학습이 독립적으로 진행됩니다.",
        progressions=_DEFAULT_PROGRESSIONS,
    ),
}


@tracks_router.get("", response_model=TracksResponse, summary="List the two learning categories")
def list_tracks(user: CurrentUser = Depends(get_current_user)) -> TracksResponse:
    return TracksResponse(items=list(_TRACK_CATALOG.values()))


@tracks_router.get("/{track_id}", response_model=Track, summary="Get category detail")
def get_track(track_id: str, user: CurrentUser = Depends(get_current_user)) -> Track:
    track = _TRACK_CATALOG.get(track_id)
    if not track:
        raise NotFoundError(f"Unknown track_id '{track_id}'.")
    return track


@tracks_router.get(
    "/{track_id}/progressions/{kind}/levels",
    response_model=LevelsResponse,
    summary="List levels in a specific progression",
)
def list_progression_levels(
    track_id: str,
    kind: ProgressionKind,
    user: CurrentUser = Depends(get_current_user),
) -> LevelsResponse:
    if track_id not in _TRACK_CATALOG:
        raise NotFoundError(f"Unknown track_id '{track_id}'.")
    items = [
        Level(
            track_id=track_id,
            kind=kind,
            level=i,
            label=f"학습 레벨 {i}",
            unlocked=i <= 1,
            total_lessons=10,
        )
        for i in range(1, 11)
    ]
    return LevelsResponse(items=items)


@me_learning_router.get("", response_model=MyLearningState, summary="My current levels and TOPIK target")
def get_my_learning(user: CurrentUser = Depends(get_current_user)) -> MyLearningState:
    return MyLearningState(
        progressions=[
            MyProgressionState(track_id="trk_conversation", kind="lectures", current_level=1, total_levels=10),
            MyProgressionState(track_id="trk_conversation", kind="sentences", current_level=1, total_levels=10),
            MyProgressionState(track_id="trk_topik", kind="lectures", current_level=1, total_levels=10),
            MyProgressionState(track_id="trk_topik", kind="sentences", current_level=1, total_levels=10),
        ],
        topik_target_grade=None,
    )


@me_learning_router.patch(
    "/{track_id}/{kind}",
    response_model=MyProgressionState,
    summary="Update the current level of a progression",
)
def update_current_level(
    track_id: str,
    kind: ProgressionKind,
    payload: UpdateCurrentLevelRequest,
    user: CurrentUser = Depends(get_current_user),
) -> MyProgressionState:
    track = _TRACK_CATALOG.get(track_id)
    if not track:
        raise NotFoundError(f"Unknown track_id '{track_id}'.")
    total = next((p.total_levels for p in track.progressions if p.kind == kind), 10)
    return MyProgressionState(
        track_id=track_id,
        kind=kind,
        current_level=payload.current_level,
        total_levels=total,
    )


@me_learning_router.patch(
    "/trk_topik",
    response_model=MyLearningState,
    summary="Update TOPIK target grade (1–6)",
)
def update_topik_target(
    payload: UpdateTopikTargetRequest,
    user: CurrentUser = Depends(get_current_user),
) -> MyLearningState:
    return MyLearningState(
        progressions=[
            MyProgressionState(track_id="trk_conversation", kind="lectures", current_level=1, total_levels=10),
            MyProgressionState(track_id="trk_conversation", kind="sentences", current_level=1, total_levels=10),
            MyProgressionState(track_id="trk_topik", kind="lectures", current_level=1, total_levels=10),
            MyProgressionState(track_id="trk_topik", kind="sentences", current_level=1, total_levels=10),
        ],
        topik_target_grade=payload.target_grade,
    )


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


@lectures_router.get("", response_model=LecturesResponse, summary="List lectures for a (category, level)")
def list_lectures(
    track_id: str = Query(...),
    level: int = Query(..., ge=1),
    user: CurrentUser = Depends(get_current_user),
) -> LecturesResponse:
    if track_id not in _TRACK_CATALOG:
        raise NotFoundError(f"Unknown track_id '{track_id}'.")
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
