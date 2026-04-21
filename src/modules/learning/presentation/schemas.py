from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

TrackKind = Literal["topik", "conversation", "business", "travel", "culture"]
LectureKind = Literal["video", "reading", "listening"]


class Track(BaseModel):
    track_id: str
    kind: TrackKind
    name: str
    description: str | None = None
    total_levels: int
    enrolled: bool = False
    progress_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class TracksResponse(BaseModel):
    items: list[Track]


class Level(BaseModel):
    track_id: str
    level: int
    label: str
    unlocked: bool = False
    progress_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    completed_lessons: int = 0
    total_lessons: int = 0


class LevelsResponse(BaseModel):
    items: list[Level]


class EnrollResponse(BaseModel):
    track_id: str
    enrolled: bool
    current_level: int


class Lecture(BaseModel):
    lecture_id: str
    track_id: str
    level: int
    title: str
    kind: LectureKind
    duration_seconds: int
    thumbnail_url: str | None = None
    completed: bool = False


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


class CompletionCelebration(BaseModel):
    new_level: int
    level_label: str
    xp_earned: int
    streak_continued: bool
