from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from src.common.exceptions import NotFoundError, ValidationError
from src.common.security.auth import CurrentUser, get_current_user
from src.modules.learning.presentation.schemas import (
    TRACK_MAX_LEVEL,
    CalendarResponse,
    Lecture,
    LectureProgressRequest,
    LectureProgressResponse,
    LectureVideoResponse,
    LecturesResponse,
    Level,
    LevelUpEventsResponse,
    LevelsResponse,
    MyLearningState,
    MyTrackState,
    StatsRange,
    StatsResponse,
    Track,
    TracksResponse,
    UpdateCurrentLevelRequest,
)

tracks_router = APIRouter(prefix="/tracks", tags=["learning"])
learning_router = APIRouter(prefix="/learning", tags=["learning"])
lectures_router = APIRouter(prefix="/lectures", tags=["learning"])
me_learning_router = APIRouter(prefix="/me/learning", tags=["learning"])

_TRACK_CATALOG: dict[str, Track] = {
    "trk_conversation": Track(
        track_id="trk_conversation",
        kind="conversation",
        name="회화",
        description="일상 회화 트랙. 현재 레벨에 맞춰 문장이 추천되며, 자동 승급됩니다.",
        max_level=TRACK_MAX_LEVEL["conversation"],
        content_kind="sentences",
    ),
    "trk_topik": Track(
        track_id="trk_topik",
        kind="topik",
        name="TOPIK",
        description="TOPIK 트랙. 현재 레벨에 맞춰 문제가 추천되며, 자동 승급됩니다.",
        max_level=TRACK_MAX_LEVEL["topik"],
        content_kind="questions",
    ),
}


def _require_track(track_id: str) -> Track:
    track = _TRACK_CATALOG.get(track_id)
    if not track:
        raise NotFoundError(f"Unknown track_id '{track_id}'.")
    return track


@tracks_router.get("", response_model=TracksResponse, summary="List the two learning tracks")
def list_tracks(user: CurrentUser = Depends(get_current_user)) -> TracksResponse:
    return TracksResponse(items=list(_TRACK_CATALOG.values()))


@tracks_router.get("/{track_id}", response_model=Track, summary="Get track detail")
def get_track(track_id: str, user: CurrentUser = Depends(get_current_user)) -> Track:
    return _require_track(track_id)


@tracks_router.get(
    "/{track_id}/levels",
    response_model=LevelsResponse,
    summary="List levels available in a track",
)
def list_levels(track_id: str, user: CurrentUser = Depends(get_current_user)) -> LevelsResponse:
    track = _require_track(track_id)
    items = [
        Level(track_id=track_id, level=i, label=f"학습 레벨 {i}")
        for i in range(1, track.max_level + 1)
    ]
    return LevelsResponse(items=items)


@me_learning_router.get("", response_model=MyLearningState, summary="My current level per track")
def get_my_learning(user: CurrentUser = Depends(get_current_user)) -> MyLearningState:
    return MyLearningState(
        tracks=[
            MyTrackState(
                track_id=tid,
                kind=track.kind,
                current_level=1,
                max_level=track.max_level,
            )
            for tid, track in _TRACK_CATALOG.items()
        ]
    )


@me_learning_router.patch(
    "/{track_id}",
    response_model=MyTrackState,
    summary="Manually set the current level of a track (resets promotion progress)",
    description=(
        "Set `current_level` to any value in 1..max_level. Direction is unrestricted — users may "
        "move up or down, including revisiting a previous level (e.g. 1 → 2 → 3 → 2). Any manual "
        "change resets `level_progress_ratio` to 0 on that track; auto-promotion is re-evaluated "
        "from scratch at the new level."
    ),
)
def update_current_level(
    track_id: str,
    payload: UpdateCurrentLevelRequest,
    user: CurrentUser = Depends(get_current_user),
) -> MyTrackState:
    track = _require_track(track_id)
    if payload.current_level > track.max_level:
        raise ValidationError(
            f"current_level must be between 1 and {track.max_level} for track '{track_id}'."
        )
    return MyTrackState(
        track_id=track_id,
        kind=track.kind,
        current_level=payload.current_level,
        max_level=track.max_level,
        level_progress_ratio=0.0,
    )


@me_learning_router.get(
    "/events",
    response_model=LevelUpEventsResponse,
    summary="My level-up events (auto-promotion history)",
)
def list_level_up_events(
    type: str = Query("level_up", description="Reserved for future event kinds; only 'level_up' today."),
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> LevelUpEventsResponse:
    if type != "level_up":
        raise ValidationError("Only type='level_up' is supported.")
    return LevelUpEventsResponse(items=[])


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


@lectures_router.get("", response_model=LecturesResponse, summary="List lectures (primarily TOPIK)")
def list_lectures(
    track_id: str = Query(...),
    level: int = Query(..., ge=1),
    user: CurrentUser = Depends(get_current_user),
) -> LecturesResponse:
    _require_track(track_id)
    return LecturesResponse(items=[])


@lectures_router.get("/{lecture_id}", response_model=Lecture, summary="Get lecture detail")
def get_lecture(lecture_id: str, user: CurrentUser = Depends(get_current_user)) -> Lecture:
    from src.modules.learning.presentation.schemas import LecturePopup

    return Lecture(
        lecture_id=lecture_id,
        track_id="trk_topik",
        level=1,
        title="인사 표현",
        kind="video",
        duration_seconds=180,
        popups=[
            LecturePopup(
                popup_id=f"pop_{lecture_id}_01",
                kind="conversation_speak",
                at_second=45,
                sentence_id="sen_hello_01",
            ),
            LecturePopup(
                popup_id=f"pop_{lecture_id}_02",
                kind="topik_question",
                at_second=120,
                quiz_id="quz_hello_01",
            ),
        ],
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
