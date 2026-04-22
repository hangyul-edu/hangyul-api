from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

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


class Lecture(BaseModel):
    lecture_id: str
    track_id: str
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


class LecturesResponse(BaseModel):
    items: list[Lecture]


class LectureVideoResponse(BaseModel):
    lecture_id: str
    video_url: str = Field(description="Signed CDN URL, short-lived.")
    expires_at: datetime
    captions_url: str | None = None


class LectureProgressRequest(BaseModel):
    position_seconds: int = Field(ge=0)
    completed: bool = False


class LectureProgressResponse(BaseModel):
    lecture_id: str
    position_seconds: int
    completed: bool
    xp_earned: int = 0


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
