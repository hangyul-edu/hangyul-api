from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.common.api.progress import DailyProgress
from src.modules.sentences.presentation.schemas import AudioFormat

QuizType = Literal["multiple_choice", "fill_blank", "typing", "ordering", "listening"]
SavedQuizSort = Literal["recent", "most_incorrect", "longest_not_reviewed"]


class QuizChoice(BaseModel):
    key: str
    text: str


class QuizAudioPlayback(BaseModel):
    """Playable quiz-audio response — returned ONLY by `GET /quizzes/{quiz_id}/audio`.

    Same single-resolution-point pattern as `SentenceAudioPlayback`. Keyed by the
    quiz's own `quiz_id` — no separate audio_id.
    """

    quiz_id: str
    url: str = Field(
        description="Signed, short-lived CDN URL for the listening-quiz audio. Cached locally after first fetch."
    )
    format: AudioFormat = "mp3"
    duration_ms: int = Field(ge=0)
    expires_at: datetime


class QuizQuestion(BaseModel):
    quiz_id: str
    type: QuizType
    prompt: str
    prompt_translation: str | None = None
    has_listening_audio: bool = Field(
        default=False,
        description=(
            "True when a listening-audio asset exists (e.g. TOPIK listening questions). The URL "
            "is not embedded — clients call GET /quizzes/{quiz_id}/audio on tap, keyed by the same "
            "`quiz_id`. Per the global audio-delivery policy (§3)."
        ),
    )
    choices: list[QuizChoice] = Field(default_factory=list)
    hint: str | None = None
    level: int = Field(ge=1, le=10)

    # Per-user history — stored on every item the caller has ever seen, regardless of whether
    # they've ever answered it correctly.
    bookmarked: bool = False
    saved_at: datetime | None = Field(
        default=None,
        description="When the user saved the question via POST /quizzes/{quiz_id}/bookmark.",
    )
    attempt_count: int = Field(
        default=0, ge=0, description="Total attempts the caller has made on this question."
    )
    incorrect_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of times the caller answered this question incorrectly. Kept even if they have "
            "never answered it correctly — it's the primary signal for 'review questions I keep "
            "missing' lists."
        ),
    )
    ever_answered_correctly: bool = Field(
        default=False, description="True if the caller has ever submitted a correct answer."
    )
    last_attempted_at: datetime | None = Field(
        default=None, description="Timestamp of the most recent attempt on this question by the caller."
    )
    last_reviewed_at: datetime | None = Field(
        default=None,
        description="Timestamp of the most recent review event (attempt or re-open from the saved list).",
    )


class QuizBookmarkResponse(BaseModel):
    quiz_id: str
    bookmarked: bool


class QuizDailySetResponse(BaseModel):
    date: str = Field(description="YYYY-MM-DD")
    questions: list[QuizQuestion]


class QuizListResponse(BaseModel):
    items: list[QuizQuestion]
    total: int


class QuizAttemptRequest(BaseModel):
    answer: str = Field(description="Selected choice key, typed text, or ordered payload.")
    elapsed_ms: int = Field(ge=0)


class QuizAttemptResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    correct: bool
    correct_answer: str | None = None
    explanation: str | None = None
    xp_earned: int
    submitted_at: datetime
    # No pre-built chatbot conversation: when the attempt is wrong, the client
    # shows a chatbot-icon CTA offering an explanation. Only on user tap does the
    # client call POST /ai/conversations with context.kind="quiz_attempt",
    # attempt_id=..., reason="explain_mistake", auto_assistant_reply=true.
    daily_progress: DailyProgress | None = Field(
        default=None,
        description=(
            "Snapshot of the TOPIK daily_question_goal progress after this attempt. When `correct` "
            "is true the server has already incremented `current`; clients update the on-screen "
            "counter directly from this field without a follow-up fetch."
        ),
    )


class QuizAttempt(BaseModel):
    attempt_id: str
    quiz_id: str
    correct: bool
    submitted_at: datetime


class QuizAttemptsResponse(BaseModel):
    items: list[QuizAttempt]
    total_attempts: int
    total_correct: int
