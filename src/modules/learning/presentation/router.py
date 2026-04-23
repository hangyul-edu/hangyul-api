from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status

from src.common.exceptions import NotFoundError, ValidationError
from src.common.security.auth import CurrentUser, get_current_user
from src.modules.learning.presentation.schemas import (
    TRACK_MAX_LEVEL,
    CalendarResponse,
    Course,
    CourseDetail,
    CoursesPage,
    CoursesResponse,
    CourseWithLessons,
    Lecture,
    LectureCompletionResponse,
    LecturePage,
    LecturePlayResponse,
    LecturePopupResolved,
    LectureProgressRequest,
    LectureProgressResponse,
    LectureVideo,
    LectureVideoResponse,
    LecturesResponse,
    Level,
    LevelUpEventsResponse,
    LevelsResponse,
    MyLearningState,
    MyTrackState,
    SpeakPracticeItem,
    SpeakPracticeResponse,
    StatsRange,
    StatsResponse,
    StreakCalendarDay,
    StreakCalendarMonth,
    StreakCalendarResponse,
    StreakMotivation,
    StreakMotivationTone,
    Track,
    TracksResponse,
    UpdateCurrentLevelRequest,
)

tracks_router = APIRouter(prefix="/tracks", tags=["learning"])
learning_router = APIRouter(prefix="/learning", tags=["learning"])
lectures_router = APIRouter(prefix="/lectures", tags=["learning"])
courses_router = APIRouter(prefix="/courses", tags=["learning"])
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


@tracks_router.get(
    "/{track_id}/courses",
    response_model=CoursesPage,
    summary="Courses in a track — vertically paginated, each with a lesson preview",
    description=(
        "Powers the lesson page. Returns a vertical page of courses (default 10 per call), and "
        "each course inlines its first `lessons_per_course` lessons (default 5) with "
        "`thumbnail_url` populated so the horizontal row card can render immediately. "
        "Use `lessons_next_cursor` on each course with GET /courses/{course_id}/lessons to load "
        "the next horizontal batch as the user scrolls right-to-left. Use the top-level "
        "`next_cursor` to load more courses as the user scrolls down."
    ),
)
def list_courses_in_track(
    track_id: str,
    cursor: str | None = Query(default=None, description="Vertical pagination cursor across courses."),
    limit: int = Query(default=10, ge=1, le=50, description="Courses per vertical page."),
    lessons_per_course: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Lessons to inline on each course card (horizontal preview size).",
    ),
    user: CurrentUser = Depends(get_current_user),
) -> CoursesPage:
    _require_track(track_id)
    return CoursesPage(items=[], next_cursor=None, has_more=False)


@courses_router.get(
    "/{course_id}/lessons",
    response_model=LecturePage,
    summary="Paginated lessons inside a course (horizontal right-to-left scroll)",
    description=(
        "Returns the next page of lessons for a single course. Each item carries "
        "`thumbnail_url` plus the caller's `completed` flag. Clients pass the "
        "`lessons_next_cursor` from CoursesPage (or the previous LecturePage.next_cursor) to "
        "continue loading ~5 more lessons each scroll step."
    ),
)
def list_course_lessons(
    course_id: str,
    cursor: str | None = Query(default=None, description="Cursor returned from the previous page."),
    limit: int = Query(default=5, ge=1, le=50, description="How many lessons to return this page."),
    user: CurrentUser = Depends(get_current_user),
) -> LecturePage:
    return LecturePage(items=[], next_cursor=None, has_more=False)


@courses_router.get(
    "/{course_id}",
    response_model=CourseDetail,
    summary="Course detail — includes the ordered lesson list with per-user completion state",
)
def get_course(course_id: str, user: CurrentUser = Depends(get_current_user)) -> CourseDetail:
    sample_lessons = [
        Lecture(
            lecture_id=f"lec_{course_id}_01",
            track_id="trk_topik",
            course_id=course_id,
            level=1,
            title="인사 표현 (1)",
            kind="video",
            duration_seconds=180,
            completed=False,
        ),
        Lecture(
            lecture_id=f"lec_{course_id}_02",
            track_id="trk_topik",
            course_id=course_id,
            level=1,
            title="인사 표현 (2)",
            kind="video",
            duration_seconds=200,
            completed=False,
        ),
    ]
    return CourseDetail(
        course_id=course_id,
        track_id="trk_topik",
        title="TOPIK 1급 입문",
        description="기초 인사와 자기소개 표현을 다루는 코스입니다.",
        level=1,
        cover_image_url=None,
        lesson_count=len(sample_lessons),
        completed_lesson_count=sum(1 for lec in sample_lessons if lec.completed),
        lessons=sample_lessons,
    )


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


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    first = date(year, month, 1)
    if month == 12:
        next_first = date(year + 1, 1, 1)
    else:
        next_first = date(year, month + 1, 1)
    last = next_first - timedelta(days=1)
    return first, last


def _shift_month(year: int, month: int, delta: int) -> str:
    index = year * 12 + (month - 1) + delta
    new_year, new_month_zero = divmod(index, 12)
    return f"{new_year:04d}-{new_month_zero + 1:02d}"


def _motivation_for(streak_days: int) -> StreakMotivation:
    tone: StreakMotivationTone
    key: str
    message: str
    if streak_days <= 0:
        tone = "resting"
        key = "streak.banner.resting"
        message = "Your streak is waiting — a short session starts a new one."
    elif streak_days == 1:
        tone = "first_day"
        key = "streak.banner.first_day"
        message = "Day one — nice start! Come back tomorrow to keep it going."
    elif streak_days < 7:
        tone = "building"
        key = "streak.banner.building"
        message = f"You are shining with learning! Keep going for {streak_days} days!"
    elif streak_days < 30:
        tone = "on_fire"
        key = "streak.banner.on_fire"
        message = f"Amazing — {streak_days} days and counting. Keep the rhythm going."
    else:
        tone = "milestone"
        key = "streak.banner.milestone"
        message = f"{streak_days} days strong. You're making Korean a habit."
    return StreakMotivation(
        streak_days=streak_days, tone=tone, message_key=key, message=message
    )


@learning_router.get(
    "/streak-calendar",
    response_model=StreakCalendarResponse,
    summary="Streak calendar page — banner copy + monthly grid",
    description=(
        "Bundled payload for the continuous-learning / streak screen. Returns current & best "
        "streak, a motivational banner rendered in the caller's `users.language`, and a "
        "pre-built month grid with `studied` / `goal_achieved` / `is_today` flags per day, "
        "plus `prev_month` / `next_month` strings for the ‹ › arrows. "
        "`year` and `month` default to the caller's local today."
    ),
)
def get_streak_calendar(
    year: int | None = Query(
        default=None,
        ge=1970,
        le=9999,
        description="Calendar year (YYYY). Defaults to today's year in the caller's local timezone.",
    ),
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
        description="Calendar month (1..12). Defaults to today's month in the caller's local timezone.",
    ),
    user: CurrentUser = Depends(get_current_user),
) -> StreakCalendarResponse:
    # Real impl uses the user's local timezone for "today"; UTC here is a stand-in.
    today = datetime.now(timezone.utc).date()
    if (year is None) ^ (month is None):
        raise ValidationError("`year` and `month` must be provided together or both omitted.")
    y = year or today.year
    m = month or today.month

    first, last = _month_bounds(y, m)
    days: list[StreakCalendarDay] = []
    cursor = first
    while cursor <= last:
        days.append(
            StreakCalendarDay(
                date=cursor,
                studied=False,
                goal_achieved=False,
                is_today=(cursor == today),
                sentences_learned=0,
                lessons_completed=0,
                minutes=0,
            )
        )
        cursor += timedelta(days=1)

    month_block = StreakCalendarMonth(
        year=y,
        month=m,
        first_date=first,
        last_date=last,
        today=today if first <= today <= last else None,
        days=days,
        studied_days=sum(1 for d in days if d.studied),
        goal_achieved_days=sum(1 for d in days if d.goal_achieved),
        prev_month=_shift_month(y, m, -1),
        next_month=_shift_month(y, m, +1),
    )

    current_streak = 0
    return StreakCalendarResponse(
        current_streak=current_streak,
        best_streak=0,
        last_study_date=None,
        freeze_tokens=0,
        motivation=_motivation_for(current_streak),
        month=month_block,
    )


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
    from src.modules.learning.presentation.schemas import LectureMyPlayback, LecturePopup

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
        my_playback=LectureMyPlayback(
            last_position_seconds=0,
            last_watched_at=datetime.now(timezone.utc),
            completed=False,
        ),
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
    summary="Report playback progress (heartbeat)",
    description=(
        "Periodic heartbeat while the user is watching. Use POST /lectures/{lecture_id}/complete "
        "to mark the lecture finished — this endpoint does not write completion."
    ),
)
def report_lecture_progress(
    lecture_id: str,
    payload: LectureProgressRequest,
    user: CurrentUser = Depends(get_current_user),
) -> LectureProgressResponse:
    return LectureProgressResponse(
        lecture_id=lecture_id,
        position_seconds=payload.position_seconds,
        last_watched_at=datetime.now(timezone.utc),
        completed=False,
    )


@lectures_router.get(
    "/{lecture_id}/play",
    response_model=LecturePlayResponse,
    summary="Open a lesson for playback — bundled video + modals + resume position",
    description=(
        "Single call the player uses to start a lesson. Returns the signed HLS URL, the ordered "
        "popup schedule with each modal's payload already resolved (Sentence for "
        "`conversation_speak`, QuizQuestion for `topik_question`), and the caller's resume offset. "
        "The client seeks to `my_playback.last_position_seconds` and begins streaming. Modals fire "
        "against the inline payloads — no extra round trips for Sentence or QuizQuestion fetches."
    ),
)
def play_lecture(
    lecture_id: str, user: CurrentUser = Depends(get_current_user)
) -> LecturePlayResponse:
    from datetime import timedelta
    from src.modules.quizzes.presentation.schemas import QuizChoice, QuizQuestion
    from src.modules.sentences.presentation.schemas import Sentence, SentenceAudioMeta

    lecture = get_lecture(lecture_id, user)
    video_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    resolved: list[LecturePopupResolved] = []
    for p in lecture.popups:
        if p.kind == "conversation_speak" and p.sentence_id:
            resolved.append(
                LecturePopupResolved(
                    popup_id=p.popup_id,
                    kind="conversation_speak",
                    at_second=p.at_second,
                    sentence=Sentence(
                        sentence_id=p.sentence_id,
                        korean="안녕하세요.",
                        display_text="안녕___.",
                        translation="Hello.",
                        translation_language="en",
                        level=lecture.level,
                        # Metadata only — client resolves the URL on tap via
                        # GET /sentences/{sentence_id}/audio keyed by p.sentence_id.
                        audio=SentenceAudioMeta(duration_ms=1800),
                    ),
                )
            )
        elif p.kind == "topik_question" and p.quiz_id:
            resolved.append(
                LecturePopupResolved(
                    popup_id=p.popup_id,
                    kind="topik_question",
                    at_second=p.at_second,
                    question=QuizQuestion(
                        quiz_id=p.quiz_id,
                        type="multiple_choice",
                        prompt="다음 중 맞는 것을 고르세요.",
                        level=lecture.level,
                        choices=[
                            QuizChoice(key="1", text="덕분에"),
                            QuizChoice(key="2", text="동안"),
                            QuizChoice(key="3", text="처럼"),
                            QuizChoice(key="4", text="만큼"),
                        ],
                    ),
                )
            )

    return LecturePlayResponse(
        lecture_id=lecture_id,
        track_id=lecture.track_id,
        course_id=lecture.course_id,
        title=lecture.title,
        video=LectureVideo(
            url=f"https://cdn.example.com/lectures/{lecture_id}/hls.m3u8?token=...",
            expires_at=video_expiry,
            captions_url=None,
            duration_seconds=lecture.duration_seconds,
        ),
        popups=resolved,
        my_playback=lecture.my_playback,
    )


@lectures_router.get(
    "/{lecture_id}/speak-practice",
    response_model=SpeakPracticeResponse,
    summary="Speak-only practice set for a lesson (filters conversation_speak popups)",
    description=(
        "Returns the `conversation_speak` popups from this lesson, in playback order, for the "
        "'mic button next to a lesson' → 'practice just the repeat-after-me sentences' flow. Each "
        "item carries popup_id, at_second, and sentence_id. The client fetches the full Sentence "
        "via GET /sentences/{sentence_id} and submits attempts through "
        "POST /sentences/{sentence_id}/speech-attempts."
    ),
)
def get_speak_practice(
    lecture_id: str, user: CurrentUser = Depends(get_current_user)
) -> SpeakPracticeResponse:
    lecture = get_lecture(lecture_id, user)
    items = [
        SpeakPracticeItem(popup_id=p.popup_id, at_second=p.at_second, sentence_id=p.sentence_id or "")
        for p in lecture.popups
        if p.kind == "conversation_speak" and p.sentence_id is not None
    ]
    return SpeakPracticeResponse(lecture_id=lecture_id, items=items)


@lectures_router.post(
    "/{lecture_id}/complete",
    response_model=LectureCompletionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mark the lecture as finished watching",
    description=(
        "Called by the client once the user has watched the lecture in full. Idempotent — a second "
        "call returns already_completed=true and xp_earned=0. Triggers TOPIK auto-promotion "
        "evaluation when applicable."
    ),
)
def complete_lecture(
    lecture_id: str, user: CurrentUser = Depends(get_current_user)
) -> LectureCompletionResponse:
    return LectureCompletionResponse(
        lecture_id=lecture_id,
        completed=True,
        already_completed=False,
        xp_earned=15,
        completed_at=datetime.now(timezone.utc),
        level_up_event=None,
    )
