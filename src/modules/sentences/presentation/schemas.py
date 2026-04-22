from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.common.api.pagination import CursorPage

SentenceStatus = Literal["new", "learning", "mastered", "bookmarked"]
AudioFormat = Literal["mp3", "wav", "aac", "opus"]
SpeechFeedback = Literal["correct", "missed_words", "bad_pronunciation", "unclear_audio"]


class SentenceExample(BaseModel):
    korean: str
    romanization: str | None = None
    translation: str
    audio_url: str | None = None


class SentenceBlank(BaseModel):
    index: int = Field(ge=0, description="0-based blank order in `display_text`.")
    answer: str = Field(description="The expected text that fills this blank.")
    start: int | None = Field(
        default=None, description="Character offset of the blank's start in `display_text`, if known."
    )
    length: int | None = Field(default=None, description="Length of the blank's placeholder in `display_text`.")


class SentenceAudio(BaseModel):
    url: str = Field(
        description=(
            "Signed, short-lived CDN URL for AI-generated TTS of the full sentence. "
            "Clients should cache the file locally and reuse it for the replay button."
        )
    )
    format: AudioFormat = "mp3"
    duration_ms: int = Field(ge=0)
    voice: str | None = Field(default=None, description="Optional TTS voice identifier.")
    expires_at: datetime


class Sentence(BaseModel):
    sentence_id: str
    korean: str = Field(description="Full correct sentence. Used for TTS and speech evaluation.")
    display_text: str | None = Field(
        default=None,
        description=(
            "Sentence as shown to the user, possibly containing blanks — e.g. '덕분에 잘 ___ 있어요'. "
            "When null, display `korean` directly."
        ),
    )
    blanks: list[SentenceBlank] = Field(default_factory=list)
    romanization: str | None = None
    translation: str
    topic: str | None = None
    level: int = Field(ge=1, le=10)
    audio: SentenceAudio | None = Field(
        default=None,
        description=(
            "AI-generated pronunciation of the full sentence. "
            "Always populated on items returned by /recommendations/sentences; optional elsewhere."
        ),
    )
    grammar_points: list[str] = Field(default_factory=list)
    examples: list[SentenceExample] = Field(default_factory=list)
    bookmarked: bool = False
    status: SentenceStatus = "new"
    last_studied_at: datetime | None = None


class SentencePage(CursorPage[Sentence]):
    pass


class BookmarkResponse(BaseModel):
    sentence_id: str
    bookmarked: bool


class ListenEventRequest(BaseModel):
    position_ms: int = 0
    completed: bool = False


class ListenEventResponse(BaseModel):
    sentence_id: str
    play_count: int


class AudioUrlResponse(BaseModel):
    sentence_id: str
    audio: SentenceAudio


class SpeechAttemptResponse(BaseModel):
    attempt_id: str
    sentence_id: str
    correct: bool = Field(description="True iff the spoken reading was accepted.")
    transcription: str = Field(
        description="What the user actually pronounced, as transcribed by the server ASR."
    )
    target_text: str = Field(description="The reference sentence (`Sentence.korean`) the user was asked to read.")
    pronunciation_score: int = Field(ge=0, le=100, description="Phoneme-level pronunciation accuracy.")
    feedback_code: SpeechFeedback = Field(
        description=(
            "Drives the client message: 'correct' → blue OK banner; anything else → red 'think again & retry' banner."
        ),
    )
    submitted_at: datetime
