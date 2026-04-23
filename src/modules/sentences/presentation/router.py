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
    SaveTypeFilter,
    SavedSentenceCounts,
    SavedSentenceDeleteResponse,
    SavedSentenceDetail,
    SavedSentenceListItem,
    SavedSentenceSortKey,
    SavedSentenceViewResponse,
    SavedSentencesPage,
    Sentence,
    SentenceAudio,
    SentencePage,
    SpeechAttemptResponse,
    WrongAnswerRequest,
    WrongAnswerResponse,
)

router = APIRouter(prefix="/sentences", tags=["sentences"])
saved_sentences_router = APIRouter(prefix="/saved-sentences", tags=["sentences"])


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
        translation_language="en",
        level=3,
        grammar_points=["덕분에"],
        audio=_stub_audio(sentence_id),
    )


@router.post(
    "/{sentence_id}/bookmark",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Favorite a sentence (sets the 'favorite' flag on the SavedSentence record)",
    description=(
        "Adds the 'favorite' flag to the caller's SavedSentence record for this sentence. If no "
        "record exists, one is created with `save_types=['favorite']` and `sources=['manual']`. "
        "If a record already exists (e.g. previously auto-saved after a wrong answer), the "
        "'favorite' flag is added — the record is never duplicated. See §4.7 Saved sentences."
    ),
)
def add_bookmark(sentence_id: str, user: CurrentUser = Depends(get_current_user)) -> BookmarkResponse:
    return BookmarkResponse(sentence_id=sentence_id, bookmarked=True)


@router.delete(
    "/{sentence_id}/bookmark",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfavorite a sentence (clears the 'favorite' flag on the SavedSentence record)",
    description=(
        "Clears the 'favorite' flag. If 'auto_wrong' remains set, the record survives and is still "
        "returned by GET /saved-sentences?save_type=auto_wrong. If no flag remains, the record is "
        "deleted entirely."
    ),
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
    from src.common.api.progress import DailyProgress

    resets = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return SpeechAttemptResponse(
        attempt_id=f"spk_{uuid4().hex[:12]}",
        sentence_id=sentence_id,
        correct=True,
        transcription="덕분에 잘 지내고 있어요.",
        target_text="덕분에 잘 지내고 있어요.",
        pronunciation_score=92,
        feedback_code="correct",
        submitted_at=datetime.now(timezone.utc),
        daily_progress=DailyProgress(
            track_id="trk_conversation",
            goal_key="daily_sentences",
            target=10,
            current=1,
            achieved=False,
            resets_at=resets,
        ),
    )


# --- Saved-sentences (unified: auto-saved + favorited) -----------------------


def _stub_saved_row(
    sentence_id: str,
    *,
    save_types: list[str] | None = None,
    sources: list[str] | None = None,
) -> SavedSentenceListItem:
    now = datetime.now(timezone.utc)
    return SavedSentenceListItem(
        sentence_id=sentence_id,
        korean="덕분에 잘 지내고 있어요.",
        translation="Thanks to you, I'm doing well.",
        translation_language="en",
        level=3,
        save_types=save_types or ["favorite"],
        is_auto_saved="auto_wrong" in (save_types or []),
        is_favorited="favorite" in (save_types or []),
        sources=sources or ["manual"],
        primary_source=(sources or ["manual"])[0] if sources or ["manual"] else None,
        wrong_count=0,
        last_viewed_at=None,
        created_at=now - timedelta(days=3),
        updated_at=now,
        has_audio=True,
        audio_id=f"aud_{sentence_id}",
    )


@saved_sentences_router.get(
    "",
    response_model=SavedSentencesPage,
    summary="Unified saved-sentences list (auto-saved + favorited)",
    description=(
        "Returns the caller's saved sentences in one stream. Filter with `save_type` ('all' = "
        "default, 'auto_wrong' = only records auto-saved after wrong answers, 'favorite' = only "
        "manually bookmarked records). Free-text search via `q` matches Korean and translation. "
        "Sort with `sort`: 'latest' (updated_at desc — new wrong answers and favorite flips both "
        "bubble up), 'most_wrong' (wrong_count desc, updated_at tiebreaker), "
        "'least_recently_viewed' (last_viewed_at asc, nulls first so never-opened items surface). "
        "The `counts` block always reports totals for the current `q` across every bucket so the "
        "segmented-control badges render without a second call."
    ),
)
def list_saved_sentences(
    save_type: SaveTypeFilter = Query(
        "all", description="Filter by flag bucket. 'all' returns records with any flag set."
    ),
    sort: SavedSentenceSortKey = Query(
        "latest", description="Sort key. Defaults to 'latest'."
    ),
    q: str | None = Query(
        default=None,
        max_length=200,
        description="Keyword search — case-insensitive prefix/substring match on Korean and translation.",
    ),
    cursor: str | None = Query(default=None, description="Opaque pagination cursor."),
    limit: int = Query(30, ge=1, le=100, description="Page size. Tuned for mobile list views."),
    user: CurrentUser = Depends(get_current_user),
) -> SavedSentencesPage:
    return SavedSentencesPage(
        items=[],
        next_cursor=None,
        has_more=False,
        counts=SavedSentenceCounts(total=0, auto_wrong=0, favorite=0, both=0),
        sort=sort,
        save_type=save_type,
        q=q,
    )


@saved_sentences_router.get(
    "/{sentence_id}",
    response_model=SavedSentenceDetail,
    summary="Saved-sentence detail (includes full Sentence + signed audio URL)",
    description=(
        "Detail payload for the practice screen the user lands on after tapping a row. Includes "
        "the hydrated `Sentence` with `audio`, grammar points, examples, blanks, and per-user "
        "history, plus the forward-compatible `tags`, `folder_id`, `priority`, `last_studied_at`, "
        "`sr_due_at`, and `review_count` fields. Fetching this endpoint does **not** count as a "
        "view — call POST /saved-sentences/{id}/view explicitly when the user opens a row."
    ),
)
def get_saved_sentence(
    sentence_id: str, user: CurrentUser = Depends(get_current_user)
) -> SavedSentenceDetail:
    row = _stub_saved_row(sentence_id)
    sentence = Sentence(
        sentence_id=sentence_id,
        korean=row.korean,
        display_text="덕분에 잘 ___ 있어요.",
        translation=row.translation,
        translation_language=row.translation_language,
        level=row.level,
        grammar_points=["덕분에"],
        audio=_stub_audio(sentence_id),
        bookmarked=row.is_favorited,
        saved_at=row.created_at,
        incorrect_count=row.wrong_count,
        last_reviewed_at=row.last_viewed_at,
    )
    return SavedSentenceDetail(
        **row.model_dump(),
        sentence=sentence,
        tags=[],
        folder_id=None,
        priority=None,
        last_studied_at=None,
        sr_due_at=None,
        review_count=0,
    )


@saved_sentences_router.post(
    "/wrong-answer",
    response_model=WrongAnswerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a wrong-answer event — auto-save or increment the existing saved record",
    description=(
        "Called by learning clients whenever the user answers incorrectly in a context that should "
        "feed the Saved Sentences list (lecture popup, recommendation practice, quiz popup). "
        "Server behavior is strictly upsert: if no record exists for (user, sentence), creates one "
        "with `save_types=['auto_wrong']`, `sources=[source]`, `wrong_count=1`. If a record exists, "
        "adds 'auto_wrong' to `save_types` (idempotent), adds `source` to `sources` if new, "
        "increments `wrong_count`, and refreshes `updated_at`. No duplicate rows are ever created. "
        "Speech-attempt submissions with `correct=false` implicitly trigger the same upsert; this "
        "endpoint is for contexts (TOPIK popup on a sentence, offline sync) where the client "
        "records the event separately."
    ),
)
def record_wrong_answer(
    payload: WrongAnswerRequest, user: CurrentUser = Depends(get_current_user)
) -> WrongAnswerResponse:
    now = datetime.now(timezone.utc)
    return WrongAnswerResponse(
        sentence_id=payload.sentence_id,
        created=True,
        wrong_count=1,
        save_types=["auto_wrong"],
        sources=[payload.source],
        updated_at=payload.occurred_at or now,
    )


@saved_sentences_router.post(
    "/{sentence_id}/view",
    response_model=SavedSentenceViewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record that the user opened / reviewed a saved sentence",
    description=(
        "Called when the user taps a saved-sentence row and the detail screen is shown. Updates "
        "`last_viewed_at` on the record so 'least_recently_viewed' sort reflects reality. Safe to "
        "call multiple times; each call overwrites `last_viewed_at` with server time."
    ),
)
def mark_saved_sentence_viewed(
    sentence_id: str, user: CurrentUser = Depends(get_current_user)
) -> SavedSentenceViewResponse:
    now = datetime.now(timezone.utc)
    return SavedSentenceViewResponse(sentence_id=sentence_id, last_viewed_at=now, updated_at=now)


@saved_sentences_router.delete(
    "/{sentence_id}/auto-save",
    response_model=SavedSentenceDeleteResponse,
    summary="Clear only the 'auto_wrong' flag — remove from auto-saved history",
    description=(
        "Removes the 'auto_wrong' flag on the record. If 'favorite' is still set, the record stays "
        "(the user still has it as a manual favorite) and `record_deleted=false`. If no flag "
        "remains, the record is deleted entirely and `record_deleted=true`. Use this when the user "
        "wants the sentence out of their auto-saved tab without losing a manual favorite."
    ),
)
def clear_auto_save(
    sentence_id: str, user: CurrentUser = Depends(get_current_user)
) -> SavedSentenceDeleteResponse:
    return SavedSentenceDeleteResponse(
        sentence_id=sentence_id, record_deleted=True, save_types=[]
    )


@saved_sentences_router.delete(
    "/{sentence_id}",
    response_model=SavedSentenceDeleteResponse,
    summary="Delete the whole saved-sentence record (clear every flag)",
    description=(
        "Hard-removes the record regardless of which flags are set. Equivalent to clearing both "
        "'auto_wrong' and 'favorite'. Returns `record_deleted=true` and an empty `save_types`. A "
        "404 is returned when no saved record exists for the caller + sentence pair."
    ),
)
def delete_saved_sentence(
    sentence_id: str, user: CurrentUser = Depends(get_current_user)
) -> SavedSentenceDeleteResponse:
    return SavedSentenceDeleteResponse(
        sentence_id=sentence_id, record_deleted=True, save_types=[]
    )
