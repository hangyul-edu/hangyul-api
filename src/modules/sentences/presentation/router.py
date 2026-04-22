from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.sentences.presentation.schemas import (
    AudioUrlResponse,
    BookmarkResponse,
    ListenEventRequest,
    ListenEventResponse,
    Sentence,
    SentenceAudio,
    SentencePage,
    SpeechAttemptResponse,
)

router = APIRouter(prefix="/sentences", tags=["sentences"])


def _stub_audio(sentence_id: str) -> SentenceAudio:
    return SentenceAudio(
        url=f"https://cdn.example.com/audio/{sentence_id}.mp3?token=...",
        format="mp3",
        duration_ms=2400,
        voice="ko-KR-ai-warm",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )


@router.get("", response_model=SentencePage, summary="List sentences for study (Conversation track)")
def list_sentences(
    level: int | None = Query(
        None, ge=1, le=10, description="Defaults to the caller's Conversation current_level."
    ),
    topic: str | None = None,
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> SentencePage:
    return SentencePage(items=[], next_cursor=None, has_more=False)


@router.get("/bookmarks", response_model=SentencePage, summary="List bookmarked sentences")
def list_bookmarks(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> SentencePage:
    return SentencePage(items=[], next_cursor=None, has_more=False)


@router.get("/recently-studied", response_model=SentencePage, summary="Recently studied sentences")
def list_recent(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> SentencePage:
    return SentencePage(items=[], next_cursor=None, has_more=False)


@router.get("/{sentence_id}", response_model=Sentence, summary="Get sentence detail (includes AI-TTS audio)")
def get_sentence(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> Sentence:
    return Sentence(
        sentence_id=sentence_id,
        korean="덕분에 잘 지내고 있어요.",
        display_text="덕분에 잘 ___ 있어요.",
        translation="Thanks to you, I'm doing well.",
        level=3,
        grammar_points=["덕분에"],
        audio=_stub_audio(sentence_id),
    )


@router.post(
    "/{sentence_id}/bookmark",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a bookmark",
)
def add_bookmark(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> BookmarkResponse:
    return BookmarkResponse(sentence_id=sentence_id, bookmarked=True)


@router.delete(
    "/{sentence_id}/bookmark",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a bookmark",
)
def remove_bookmark(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@router.post(
    "/{sentence_id}/listen",
    response_model=ListenEventResponse,
    summary="Report audio playback event (for analytics / auto-promotion signal)",
)
def report_listen(
    sentence_id: str,
    payload: ListenEventRequest,
    user: CurrentUser = Depends(get_current_user),
) -> ListenEventResponse:
    return ListenEventResponse(sentence_id=sentence_id, play_count=1)


@router.get(
    "/{sentence_id}/audio",
    response_model=AudioUrlResponse,
    summary="Refresh the signed audio URL (e.g. after the cached one expired)",
)
def get_audio_url(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> AudioUrlResponse:
    return AudioUrlResponse(sentence_id=sentence_id, audio=_stub_audio(sentence_id))


@router.post(
    "/{sentence_id}/speech-attempts",
    response_model=SpeechAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the user's spoken reading of the sentence for AI evaluation",
    description=(
        "Multipart upload. `audio` is the raw recording (wav / mp3 / m4a / webm / opus, ≤ 2 MB, "
        "≤ 15 s). The server runs ASR + pronunciation scoring against the reference sentence and "
        "returns `correct`, the transcription, a 0–100 pronunciation score, and a `feedback_code` "
        "that the client renders as blue (correct) or red (think again) messaging."
    ),
)
def submit_speech_attempt(
    sentence_id: str,
    audio: UploadFile = File(..., description="Raw recording, ≤ 2 MB and ≤ 15 s."),
    duration_ms: int | None = Form(default=None, description="Client-reported duration in milliseconds."),
    client_request_id: str | None = Form(default=None, description="Optional idempotency key."),
    user: CurrentUser = Depends(get_current_user),
) -> SpeechAttemptResponse:
    return SpeechAttemptResponse(
        attempt_id=f"spk_{uuid4().hex[:12]}",
        sentence_id=sentence_id,
        correct=True,
        transcription="덕분에 잘 지내고 있어요.",
        target_text="덕분에 잘 지내고 있어요.",
        pronunciation_score=92,
        feedback_code="correct",
        submitted_at=datetime.now(timezone.utc),
    )
