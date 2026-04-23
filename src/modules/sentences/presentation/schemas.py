from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.common.api.pagination import CursorPage
from src.common.api.progress import DailyProgress

SentenceStatus = Literal["new", "learning", "mastered", "bookmarked"]
AudioFormat = Literal["mp3", "wav", "aac", "opus"]
SpeechFeedback = Literal["correct", "missed_words", "bad_pronunciation", "unclear_audio"]

# --- Saved-sentence taxonomy ---------------------------------------------------
# `SaveType` is a *flag* set — one record can carry multiple reasons for being
# saved. `SavedSource` records where the save originated (first wrong answer
# location or the manual-favorite context). A record exists as long as at
# least one SaveType flag is set; clearing the last flag deletes the row.

SaveType = Literal["auto_wrong", "favorite"]
SavedSource = Literal["lecture", "recommendation", "quiz_popup", "manual"]
SavedSentenceSortKey = Literal["latest", "most_wrong", "least_recently_viewed"]
SaveTypeFilter = Literal["all", "auto_wrong", "favorite"]


class SentenceExample(BaseModel):
    korean: str
    romanization: str | None = None
    translation: str


class SentenceBlank(BaseModel):
    index: int = Field(ge=0, description="0-based blank order in `display_text`.")
    answer: str = Field(description="The expected text that fills this blank.")
    start: int | None = Field(
        default=None, description="Character offset of the blank's start in `display_text`, if known."
    )
    length: int | None = Field(default=None, description="Length of the blank's placeholder in `display_text`.")


class SentenceAudioMeta(BaseModel):
    """Lightweight audio metadata — embedded in normal responses.

    Intentionally carries **no URL and no expiry**. Clients resolve the playable
    URL on tap via `GET /sentences/{sentence_id}/audio`, keyed by the sentence's
    own id (no separate audio_id — sentences reused across features share a
    single audio asset). See §3 "Audio delivery" in the functional spec.
    """

    format: AudioFormat = "mp3"
    duration_ms: int = Field(ge=0, description="Playback length — useful for UI progress bars before the file is fetched.")
    voice: str | None = Field(default=None, description="Optional TTS voice identifier.")


class SentenceAudioPlayback(BaseModel):
    """Playable audio response — returned ONLY by `GET /sentences/{sentence_id}/audio`.

    This is the one shape that carries a signed, short-lived URL. Every other
    response that mentions audio uses `SentenceAudioMeta` (metadata only).
    """

    sentence_id: str = Field(description="The sentence this URL plays. Same key used everywhere else.")
    url: str = Field(
        description=(
            "Signed, short-lived CDN URL for AI-generated TTS of the full sentence. Clients cache "
            "the downloaded file locally and reuse it for replay; they only re-hit this endpoint "
            "when the cached file or URL has expired."
        )
    )
    format: AudioFormat = "mp3"
    duration_ms: int = Field(ge=0)
    voice: str | None = None
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
    translation: str = Field(
        description="Meaning of the Korean sentence, rendered in the caller's default language."
    )
    translation_language: str = Field(
        description=(
            "BCP-47 code of `translation` — mirrors the caller's `users.language` (e.g. 'en', 'ja', "
            "'zh-CN'). The server regenerates the translation whenever that preference changes."
        ),
    )
    topic: str | None = None
    level: int = Field(ge=1, le=10)
    audio: SentenceAudioMeta | None = Field(
        default=None,
        description=(
            "Metadata-only descriptor of the AI-generated pronunciation audio — `format`, "
            "`duration_ms`, `voice`. Non-null whenever a playable asset exists. The playable URL "
            "is NOT included here; the client fetches it on tap via "
            "GET /sentences/{sentence_id}/audio. Always populated on items returned by "
            "/recommendations/sentences; null elsewhere only when no audio exists."
        ),
    )
    grammar_points: list[str] = Field(default_factory=list)
    examples: list[SentenceExample] = Field(default_factory=list)
    bookmarked: bool = False
    status: SentenceStatus = "new"
    last_studied_at: datetime | None = None
    saved_at: datetime | None = Field(
        default=None,
        description=(
            "When the user saved this sentence via POST /sentences/{sentence_id}/bookmark. Null when "
            "not saved. Populated on every response that carries a saved sentence."
        ),
    )
    attempt_count: int = Field(
        default=0,
        ge=0,
        description="Total number of speech-attempts the caller has made on this sentence.",
    )
    incorrect_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of times the user got this sentence wrong on speech-attempts. Stored "
            "regardless of whether they ever answered correctly. Powers the "
            "'most frequently answered incorrectly' sort on the saved list."
        ),
    )
    ever_answered_correctly: bool = Field(
        default=False,
        description="True if the user has produced at least one `correct=true` speech-attempt on this sentence.",
    )
    last_reviewed_at: datetime | None = Field(
        default=None,
        description=(
            "Most recent review event — successful speech attempt, listen, or re-open from the saved "
            "list. Used to power the 'longest not reviewed' sort."
        ),
    )


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


class AudioUrlResponse(SentenceAudioPlayback):
    """Response of `GET /sentences/{sentence_id}/audio` — the sole source of signed audio URLs.

    Flat shape (extends `SentenceAudioPlayback`) so clients don't need to unwrap a nested object.
    """


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
    daily_progress: DailyProgress | None = Field(
        default=None,
        description=(
            "Snapshot of the Conversation daily_sentence_goal progress after this attempt. When "
            "`correct` is true the server has already incremented `current`; clients update the "
            "on-screen counter directly from this field."
        ),
    )


# --- Saved sentences ----------------------------------------------------------
# One `SavedSentence` per (user, sentence). The record carries a *set* of
# `save_types` flags — "auto_wrong" (saved automatically after an incorrect
# attempt) and/or "favorite" (user manually bookmarked). A sentence that is
# first auto-saved and later favorited becomes a single record with both
# flags set; there are never duplicate rows. Mobile list rows are lean
# (no inline audio URL) — the detail endpoint resolves the signed URL.


class SavedSentenceListItem(BaseModel):
    sentence_id: str = Field(description="Canonical sentence id — also the saved record's key for the caller.")
    korean: str = Field(description="Full Korean text (as shown in the list row).")
    translation: str = Field(
        description="Meaning of `korean`, rendered in the caller's `users.language`."
    )
    translation_language: str = Field(description="BCP-47 code of `translation` (mirrors `users.language`).")
    level: int = Field(ge=1, le=10)

    save_types: list[SaveType] = Field(
        description=(
            "Set of active save-type flags — the list is deduped and may carry one or both of "
            "'auto_wrong' (saved by the system after a wrong attempt) and 'favorite' (manually "
            "bookmarked by the user)."
        ),
    )
    is_auto_saved: bool = Field(description="Convenience: `'auto_wrong' in save_types`.")
    is_favorited: bool = Field(description="Convenience: `'favorite' in save_types`.")

    sources: list[SavedSource] = Field(
        default_factory=list,
        description=(
            "Where the auto-saves originated — any of 'lecture', 'recommendation', 'quiz_popup', "
            "'manual'. A pure manual favorite carries just 'manual'; an auto-save from a lecture "
            "popup carries 'lecture'; a record that was auto-saved first and then favorited may "
            "carry both. Ordered by first-seen."
        ),
    )
    primary_source: SavedSource | None = Field(
        default=None,
        description="The earliest source in `sources`; useful for a single-tag display on the list row.",
    )

    wrong_count: int = Field(
        ge=0,
        default=0,
        description="Accumulated wrong-answer count across all attempt contexts. Drives the 'most_wrong' sort.",
    )
    last_viewed_at: datetime | None = Field(
        default=None,
        description=(
            "Most recent time the user opened / reviewed the saved sentence via "
            "POST /saved-sentences/{id}/view. Null when never opened from the saved list — drives "
            "'least_recently_viewed' sort (nulls surface first)."
        ),
    )
    created_at: datetime = Field(description="When the saved record was first created.")
    updated_at: datetime = Field(
        description=(
            "Timestamp of the most recent mutation to the record: a new wrong answer, a favorite "
            "flag flip, a view, or any other state change. Drives the 'latest' sort."
        ),
    )

    has_audio: bool = Field(
        default=False,
        description=(
            "True when a TTS audio asset exists for this sentence. The list never carries a URL; "
            "the client resolves it on tap via GET /sentences/{sentence_id}/audio, keyed by the "
            "same `sentence_id` shown on this row. No separate audio_id is used — sentences reused "
            "across features share one audio asset under their canonical sentence id."
        ),
    )


class SavedSentenceCounts(BaseModel):
    total: int = Field(ge=0, description="Records matching the caller's query (after `q` / `save_type` filter).")
    auto_wrong: int = Field(ge=0, description="Records carrying the 'auto_wrong' flag (may overlap with 'favorite').")
    favorite: int = Field(ge=0, description="Records carrying the 'favorite' flag.")
    both: int = Field(ge=0, description="Records carrying both flags — useful for a 'merged' badge count.")


class SavedSentencesPage(BaseModel):
    items: list[SavedSentenceListItem]
    next_cursor: str | None = None
    has_more: bool = False
    counts: SavedSentenceCounts = Field(
        description=(
            "Per-bucket counts for the current `q` search, ignoring the `save_type` filter — so the "
            "UI can render the segmented-control badges (e.g. 'All 42 · Auto 31 · Favorites 18') "
            "without a second round trip."
        ),
    )
    sort: SavedSentenceSortKey
    save_type: SaveTypeFilter
    q: str | None = None


class SavedSentenceDetail(SavedSentenceListItem):
    """Detail response — extends the list item with the full `Sentence` payload + forward-compatible extension fields."""

    sentence: Sentence = Field(
        description=(
            "Fully hydrated Sentence, including the signed `audio` URL, grammar points, examples, "
            "and blanks. Use this to render the practice screen when the user taps a saved row."
        ),
    )
    # Forward-compatible fields — reserved for future releases; always present (may be empty / null).
    tags: list[str] = Field(default_factory=list, description="User-assigned tags (reserved for a future release).")
    folder_id: str | None = Field(default=None, description="Folder this record belongs to (reserved for a future release).")
    priority: int | None = Field(
        default=None, description="User-assigned study priority, 1 = highest (reserved for a future release)."
    )
    last_studied_at: datetime | None = Field(
        default=None,
        description="Most recent study event (speech attempt, lesson re-watch, etc.) — decoupled from `last_viewed_at`.",
    )
    sr_due_at: datetime | None = Field(
        default=None,
        description="Next spaced-repetition due date (reserved for a future release).",
    )
    review_count: int = Field(
        ge=0,
        default=0,
        description="Number of completed review events (reserved; starts at 0 in v1).",
    )


class WrongAnswerRequest(BaseModel):
    sentence_id: str = Field(description="Sentence the user answered incorrectly.")
    source: SavedSource = Field(
        description=(
            "Context of the wrong answer: 'lecture' (in-lesson modal), 'recommendation' "
            "(recommendation card practice), 'quiz_popup' (TOPIK popup that referenced a sentence). "
            "Pass 'manual' only for explicit client-driven saves with no specific context."
        ),
    )
    lecture_id: str | None = Field(
        default=None,
        description="Populated when `source == 'lecture'` so analytics and the LRU screen can deep-link back.",
    )
    quiz_id: str | None = Field(default=None, description="Populated when `source == 'quiz_popup'`.")
    occurred_at: datetime | None = Field(
        default=None,
        description="Client-supplied event timestamp (for offline sync); defaults to server time when omitted.",
    )


class WrongAnswerResponse(BaseModel):
    sentence_id: str
    created: bool = Field(
        description="True iff this call created a new saved record; false when an existing record was updated."
    )
    wrong_count: int = Field(ge=0, description="`wrong_count` after this call (pre-existing count + 1).")
    save_types: list[SaveType]
    sources: list[SavedSource]
    updated_at: datetime


class SavedSentenceViewResponse(BaseModel):
    sentence_id: str
    last_viewed_at: datetime = Field(description="The timestamp just written.")
    updated_at: datetime


class SavedSentenceDeleteResponse(BaseModel):
    sentence_id: str
    record_deleted: bool = Field(
        description=(
            "True when the entire record was removed (no flags remained). False when only the "
            "targeted flag was cleared and the record survives because another flag is still set "
            "(e.g. clearing 'auto_wrong' on a record that is still favorited)."
        ),
    )
    save_types: list[SaveType] = Field(
        description="Flags still active on the record after this call. Empty when the record was deleted."
    )
