from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LearningPurpose = Literal["conversation", "topik"]
SpeakingLevel = Literal["beginner", "elementary", "intermediate", "advanced", "fluent"]
TopikTarget = Literal["none", "1", "2", "3", "4", "5", "6"]


class OnboardingOption(BaseModel):
    code: str
    label: str
    description: str | None = None


class OnboardingQuestion(BaseModel):
    key: Literal["purpose", "speaking_level", "topik_target", "daily_goal_minutes"]
    prompt: str
    multi: bool = False
    options: list[OnboardingOption]


class OnboardingQuestionsResponse(BaseModel):
    questions: list[OnboardingQuestion]


class OnboardingSubmissionRequest(BaseModel):
    purpose: LearningPurpose
    speaking_level: SpeakingLevel
    topik_target: TopikTarget = "none"
    daily_goal_minutes: int = Field(default=10, ge=5, le=120)
    push_opt_in: bool = True


class OnboardingStatusResponse(BaseModel):
    completed: bool
    purpose: LearningPurpose | None = None
    speaking_level: SpeakingLevel | None = None
    topik_target: TopikTarget | None = None
    recommended_track_id: str | None = None
    recommended_level: int | None = None
