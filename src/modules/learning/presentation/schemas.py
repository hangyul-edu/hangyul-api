from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.common.api.pagination import CursorPage
from src.modules.quizzes.presentation.schemas import QuizQuestion
from src.modules.sentences.presentation.schemas import Sentence

TrackKind = Literal["topik", "conversation"]
LectureKind = Literal["video", "reading", "listening"]

# Level scale per track: Conversation 1..10, TOPIK 1..6.
TRACK_MAX_LEVEL: dict[TrackKind, int] = {"conversation": 10, "topik": 6}


class Track(BaseModel):
    track_id: str
    kind: TrackKind
    name: str
    description: str | None = None
    max_level: int = Field(description="Upper bound of current_level for this track.")
    content_kind: Literal["sentences", "questions"] = Field(
        description="sentences = Conversation track, questions = TOPIK track."
    )


class TracksResponse(BaseModel):
    items: list[Track]


class Level(BaseModel):
    track_id: str
    level: int
    label: str


class LevelsResponse(BaseModel):
    items: list[Level]


class MyTrackState(BaseModel):
    track_id: str
    kind: TrackKind
    current_level: int = Field(ge=1)
    max_level: int
    level_progress_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Progress toward auto-promotion at the current level (0..1). Reset to 0 by any manual "
            "level change, regardless of direction."
        ),
    )


class MyLearningState(BaseModel):
    tracks: list[MyTrackState]


class UpdateCurrentLevelRequest(BaseModel):
    current_level: int = Field(ge=1)


class LevelUpEvent(BaseModel):
    event_id: str
    track_id: str
    from_level: int = Field(ge=1)
    to_level: int = Field(ge=1)
    criterion: str = Field(description="Machine-readable reason, e.g. 'sentences_completed_threshold'.")
    occurred_at: datetime


class LevelUpEventsResponse(BaseModel):
    items: list[LevelUpEvent]
    next_cursor: str | None = None


LectureAccess = Literal["free", "premium"]
LecturePopupKind = Literal["conversation_speak", "topik_question"]


class LectureMyPlayback(BaseModel):
    last_position_seconds: int = Field(
        ge=0,
        description=(
            "How far the caller last watched. Updated by every POST /lectures/{id}/progress "
            "heartbeat. Clients seek to this offset on resume."
        ),
    )
    last_watched_at: datetime = Field(description="Timestamp of the most recent progress heartbeat.")
    completed: bool = Field(default=False, description="Mirrors Lecture.completed for convenience.")


class LecturePopup(BaseModel):
    popup_id: str = Field(description="Stable id for analytics and idempotent client replay.")
    kind: LecturePopupKind = Field(
        description=(
            "'conversation_speak' — a sentence is shown and the user must read it aloud; the client "
            "submits the recording to POST /sentences/{sentence_id}/speech-attempts. "
            "'topik_question' — a multiple-choice / typing question; submission goes to "
            "POST /quizzes/{quiz_id}/attempts."
        )
    )
    at_second: int = Field(
        ge=0, description="Playback offset (seconds) at which the popup should fire."
    )
    sentence_id: str | None = Field(
        default=None,
        description="Present iff kind == 'conversation_speak'; references the Sentence the user reads aloud.",
    )
    quiz_id: str | None = Field(
        default=None,
        description="Present iff kind == 'topik_question'; references the QuizQuestion to present.",
    )


class Lecture(BaseModel):
    lecture_id: str
    track_id: str
    course_id: str | None = Field(
        default=None,
        description=(
            "Course this lesson belongs to (Track → Course → Lesson). Null when the lesson is not "
            "grouped into a course."
        ),
    )
    level: int
    title: str
    kind: LectureKind
    duration_seconds: int
    thumbnail_url: str | None = None
    completed: bool = False
    access: LectureAccess = Field(
        default="free",
        description=(
            "'free' lectures are visible to all members. 'premium' lectures require trial or paid "
            "membership; non-premium callers get the metadata but receive 402 subscription_required "
            "when they request the video URL."
        ),
    )
    popups: list[LecturePopup] = Field(
        default_factory=list,
        description=(
            "Ordered by `at_second`. Clients render each popup as a modal at the matching playback "
            "offset. When the user has `exclude_speaking = true` in AppSettings, clients suppress "
            "popups with kind == 'conversation_speak' (topik_question popups still fire)."
        ),
    )
    my_playback: LectureMyPlayback | None = Field(
        default=None,
        description=(
            "Caller-scoped playback state. Null when the user has never started this lecture. "
            "Clients resume from `my_playback.last_position_seconds` on re-entry."
        ),
    )


class LecturesResponse(BaseModel):
    items: list[Lecture]


class Course(BaseModel):
    course_id: str
    track_id: str
    title: str
    description: str | None = None
    level: int | None = Field(
        default=None, description="Track level this course belongs to (if any)."
    )
    cover_image_url: str | None = None
    lesson_count: int = Field(ge=0)
    completed_lesson_count: int = Field(
        ge=0, description="How many lessons in the course the caller has finished."
    )


class CoursesResponse(BaseModel):
    items: list[Course]


class CourseWithLessons(Course):
    lessons_preview: list[Lecture] = Field(
        description=(
            "First `lessons_per_course` lessons in the course (default 5), each including "
            "thumbnail_url for the row card. Ordered by lesson sequence."
        ),
    )
    lessons_next_cursor: str | None = Field(
        default=None,
        description=(
            "Cursor for the horizontal scroll within this course. Null when the preview already "
            "holds every lesson. Clients load the next batch via "
            "GET /courses/{course_id}/lessons?cursor=..."
        ),
    )


class CoursesPage(BaseModel):
    items: list[CourseWithLessons]
    next_cursor: str | None = Field(
        default=None, description="Cursor for the next vertical page of courses. Null when exhausted."
    )
    has_more: bool = False


class LecturePage(CursorPage[Lecture]):
    """Horizontally-paginated lessons inside a single course."""


class CourseDetail(Course):
    lessons: list[Lecture] = Field(
        description=(
            "Ordered list of lessons (lectures) in the course. Each carries the caller's "
            "`completed` flag plus `popups[]`, so the UI can render both the lesson list with "
            "completion state and drill into any individual lesson."
        ),
    )


class SpeakPracticeItem(BaseModel):
    popup_id: str = Field(description="The originating `conversation_speak` popup on the lesson.")
    at_second: int = Field(
        ge=0, description="Offset within the lesson where the popup would have fired during normal playback."
    )
    sentence_id: str = Field(description="Sentence the user reads aloud.")


class SpeakPracticeResponse(BaseModel):
    lecture_id: str
    items: list[SpeakPracticeItem] = Field(
        description=(
            "The `conversation_speak` popups from this lesson, in playback order. The full "
            "Sentence payload (with audio, display_text, blanks, translation) is fetched via "
            "GET /sentences/{sentence_id} and the user practices each via "
            "POST /sentences/{sentence_id}/speech-attempts (see §4.7)."
        ),
    )


class LectureVideoResponse(BaseModel):
    lecture_id: str
    video_url: str = Field(description="Signed CDN URL, short-lived.")
    expires_at: datetime
    captions_url: str | None = None


# --- Lesson "play" bundle ------------------------------------------------------
# Served by GET /lectures/{lecture_id}/play. Everything the client needs to start
# streaming the video and render the in-lesson modals at the right timestamps
# without chasing per-popup lookups.


class LectureVideo(BaseModel):
    url: str = Field(description="Signed HLS playlist URL.")
    expires_at: datetime
    captions_url: str | None = None
    duration_seconds: int = Field(ge=0)


class LecturePopupResolved(BaseModel):
    popup_id: str
    kind: LecturePopupKind
    at_second: int = Field(ge=0)
    sentence: Sentence | None = Field(
        default=None,
        description=(
            "Present iff kind == 'conversation_speak'. Full Sentence payload: Korean text, "
            "display_text with blanks, translation in the caller's language, and the TTS audio — "
            "everything the modal needs, no extra fetch."
        ),
    )
    question: QuizQuestion | None = Field(
        default=None,
        description=(
            "Present iff kind == 'topik_question'. Full QuizQuestion payload with choices, "
            "prompt, prompt_translation, and per-user history — ready to render as the modal."
        ),
    )


class LecturePlayResponse(BaseModel):
    lecture_id: str
    track_id: str
    course_id: str | None = None
    title: str
    video: LectureVideo
    popups: list[LecturePopupResolved] = Field(
        description=(
            "Every modal inline — ordered by `at_second`. Conversation lessons carry sentences "
            "(with translation in users.language); TOPIK lessons carry questions. Mixed lessons "
            "may carry both."
        ),
    )
    my_playback: LectureMyPlayback | None = Field(
        default=None,
        description="Caller's resume position; the client seeks here before starting playback.",
    )


class LectureProgressRequest(BaseModel):
    position_seconds: int = Field(ge=0, description="Current playback offset in seconds. Sent periodically as a heartbeat.")


class LectureProgressResponse(BaseModel):
    lecture_id: str
    position_seconds: int = Field(description="Echoes the saved position after this heartbeat.")
    last_watched_at: datetime = Field(description="Server timestamp of the heartbeat.")
    completed: bool = Field(description="Current completion state (read-only here — set via POST /lectures/{id}/complete).")


class LectureCompletionResponse(BaseModel):
    lecture_id: str
    completed: bool = Field(description="Always true in the success response.")
    already_completed: bool = Field(
        description="True when the caller previously completed this lecture — in which case xp_earned is 0."
    )
    xp_earned: int = Field(ge=0, description="XP granted by this call. 0 on repeat completions.")
    completed_at: datetime
    level_up_event: LevelUpEvent | None = Field(
        default=None,
        description="Populated when this completion triggered TOPIK auto-promotion (see 4.6).",
    )


class CalendarDay(BaseModel):
    date: date
    minutes: int
    sentences_learned: int
    lessons_completed: int
    goal_achieved: bool


class CalendarResponse(BaseModel):
    from_date: date
    to_date: date
    days: list[CalendarDay]
    studied_days: int


StatsRange = Literal["week", "month", "year", "all"]


class StatsPoint(BaseModel):
    bucket: str = Field(description="ISO date for day, YYYY-Www for week, YYYY-MM for month")
    minutes: int
    sentences: int
    xp: int


class StatsResponse(BaseModel):
    range: StatsRange
    total_minutes: int
    total_sentences: int
    total_xp: int
    points: list[StatsPoint]
