from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

TrackKind = Literal["topik", "conversation"]
ProgressionKind = Literal["lectures", "sentences"]
LectureKind = Literal["video", "reading", "listening"]


class ProgressionInfo(BaseModel):
    kind: ProgressionKind
    total_levels: int
    level_label_prefix: str = "학습 레벨"


class Track(BaseModel):
    track_id: str
    kind: TrackKind
    name: str
    description: str | None = None
    progressions: list[ProgressionInfo]


class TracksResponse(BaseModel):
    items: list[Track]


class Level(BaseModel):
    track_id: str
    kind: ProgressionKind
    level: int
    label: str
    unlocked: bool = False
    progress_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    completed_lessons: int = 0
    total_lessons: int = 0


class LevelsResponse(BaseModel):
    items: list[Level]


class MyProgressionState(BaseModel):
    track_id: str
    kind: ProgressionKind
    current_level: int = Field(ge=1)
    total_levels: int


class MyLearningState(BaseModel):
    progressions: list[MyProgressionState]
    topik_target_grade: int | None = Field(
        default=None, ge=1, le=6, description="Only set when the user enrolled into TOPIK at onboarding."
    )


class UpdateCurrentLevelRequest(BaseModel):
    current_level: int = Field(ge=1)


class UpdateTopikTargetRequest(BaseModel):
    target_grade: int = Field(ge=1, le=6)


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
