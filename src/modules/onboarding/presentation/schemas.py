from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LearningPurpose = Literal["conversation", "topik"]
SpeakingLevel = Literal["beginner", "elementary", "intermediate", "advanced", "fluent"]
TopikTarget = Literal["none", "1", "2", "3", "4", "5", "6"]
DailyItemGoal = Literal[5, 10, 20, 30, 40]


class OnboardingOption(BaseModel):
    code: str
    label: str
    description: str | None = None


class OnboardingQuestion(BaseModel):
    key: Literal[
        "purpose",
        "speaking_level",
        "topik_target",
        "daily_sentence_goal",
        "daily_question_goal",
    ]
    prompt: str
    multi: bool = False
    options: list[OnboardingOption]


class OnboardingQuestionsResponse(BaseModel):
    questions: list[OnboardingQuestion]


class OnboardingSubmissionRequest(BaseModel):
    purpose: LearningPurpose
    speaking_level: SpeakingLevel
    topik_target: TopikTarget = Field(
        default="none", description="Required when purpose == 'topik'. Ignored otherwise."
    )
    daily_sentence_goal: DailyItemGoal | None = Field(
        default=None,
        description=(
            "Asked when purpose == 'conversation'. Daily goal for number of sentences studied; "
            "one of 5 / 10 / 20 / 30 / 40. Defaults to 10 when omitted."
        ),
    )
    daily_question_goal: DailyItemGoal | None = Field(
        default=None,
        description=(
            "Asked when purpose == 'topik'. Daily goal for number of questions attempted; "
            "one of 5 / 10 / 20 / 30 / 40. Defaults to 10 when omitted."
        ),
    )
    push_opt_in: bool = True


class OnboardingStatusResponse(BaseModel):
    completed: bool
    purpose: LearningPurpose | None = None
    speaking_level: SpeakingLevel | None = None
    topik_target: TopikTarget | None = None
    daily_sentence_goal: DailyItemGoal | None = None
    daily_question_goal: DailyItemGoal | None = None
    recommended_track_id: str | None = None
    recommended_level: int | None = None
