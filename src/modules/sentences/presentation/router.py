from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.sentences.presentation.schemas import (
    AudioUrlResponse,
    BookmarkResponse,
    ListenEventRequest,
    ListenEventResponse,
    Sentence,
    SentencePage,
)

router = APIRouter(prefix="/sentences", tags=["sentences"])


@router.get("", response_model=SentencePage, summary="List sentences for study")
def list_sentences(
    level: int | None = Query(None, ge=1, le=10),
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


@router.get("/{sentence_id}", response_model=Sentence, summary="Get sentence detail")
def get_sentence(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> Sentence:
    return Sentence(
        sentence_id=sentence_id,
        korean="덕분에 잘 지내고 있어요.",
        translation="Thanks to you, I'm doing well.",
        level=3,
        grammar_points=["덕분에"],
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
    summary="Report audio playback event",
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
    summary="Get signed audio URL for the sentence",
)
def get_audio_url(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> AudioUrlResponse:
    return AudioUrlResponse(
        sentence_id=sentence_id,
        audio_url=f"https://cdn.example.com/audio/{sentence_id}.mp3?token=...",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
