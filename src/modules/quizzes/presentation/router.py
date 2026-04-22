from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.quizzes.presentation.schemas import (
    QuizAttempt,
    QuizAttemptRequest,
    QuizAttemptResponse,
    QuizAttemptsResponse,
    QuizBookmarkResponse,
    QuizDailySetResponse,
    QuizListResponse,
    QuizQuestion,
    QuizType,
    SavedQuizSort,
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("", response_model=QuizListResponse, summary="List quiz questions")
def list_quizzes(
    type: QuizType | None = None,
    level: int | None = Query(None, ge=1, le=10),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> QuizListResponse:
    return QuizListResponse(items=[], total=0)


@router.get("/daily", response_model=QuizDailySetResponse, summary="Today's quiz set")
def get_daily(user: CurrentUser = Depends(get_current_user)) -> QuizDailySetResponse:
    return QuizDailySetResponse(date=datetime.now(timezone.utc).date().isoformat(), questions=[])


@router.get("/attempts/me", response_model=QuizAttemptsResponse, summary="My quiz attempts")
def list_my_attempts(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> QuizAttemptsResponse:
    return QuizAttemptsResponse(items=[], total_attempts=0, total_correct=0)


@router.get(
    "/bookmarks",
    response_model=QuizListResponse,
    summary="List saved (bookmarked) questions for the saved-list screen",
    description=(
        "Returns every question the caller saved. Each item carries full per-user history "
        "(bookmarked, saved_at, attempt_count, incorrect_count, ever_answered_correctly, "
        "last_attempted_at, last_reviewed_at). Sort options: `recent` (default, saved_at desc), "
        "`most_incorrect` (incorrect_count desc — works even for items the user has never gotten "
        "right), `longest_not_reviewed` (last_reviewed_at asc, null first)."
    ),
)
def list_quiz_bookmarks(
    sort: SavedQuizSort = Query("recent"),
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> QuizListResponse:
    return QuizListResponse(items=[], total=0)


@router.post(
    "/{quiz_id}/bookmark",
    response_model=QuizBookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a question to the saved list",
)
def bookmark_quiz(
    quiz_id: str, user: CurrentUser = Depends(get_current_user)
) -> QuizBookmarkResponse:
    return QuizBookmarkResponse(quiz_id=quiz_id, bookmarked=True)


@router.delete(
    "/{quiz_id}/bookmark",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a question from the saved list (idempotent 204)",
)
def unbookmark_quiz(quiz_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@router.get("/{quiz_id}", response_model=QuizQuestion, summary="Get a specific quiz question")
def get_quiz(quiz_id: str, user: CurrentUser = Depends(get_current_user)) -> QuizQuestion:
    return QuizQuestion(
        quiz_id=quiz_id,
        type="multiple_choice",
        prompt="어제 충분히 휴식을 취한 ( ) 오늘 하루도 힘차게 시작할 수 있었다.",
        level=3,
        choices=[
            {"key": "1", "text": "덕분에"},
            {"key": "2", "text": "동안"},
            {"key": "3", "text": "처럼"},
            {"key": "4", "text": "만큼"},
        ],
    )


@router.post(
    "/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a quiz answer",
)
def submit_attempt(
    quiz_id: str,
    payload: QuizAttemptRequest,
    user: CurrentUser = Depends(get_current_user),
) -> QuizAttemptResponse:
    from datetime import timedelta

    from src.common.api.progress import DailyProgress

    correct = payload.answer == "1"
    resets = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    progress = DailyProgress(
        track_id="trk_topik",
        goal_key="daily_questions",
        target=10,
        current=1 if correct else 0,
        achieved=False,
        resets_at=resets,
    )
    return QuizAttemptResponse(
        attempt_id=f"att_{uuid4().hex[:12]}",
        quiz_id=quiz_id,
        correct=correct,
        correct_answer="1",
        explanation="'덕분에'는 긍정적인 결과의 원인을 나타낼 때 사용합니다.",
        xp_earned=10 if correct else 0,
        submitted_at=datetime.now(timezone.utc),
        daily_progress=progress,
    )


@router.get(
    "/{quiz_id}/attempts/{attempt_id}",
    response_model=QuizAttemptResponse,
    summary="Get a past attempt",
)
def get_attempt(
    quiz_id: str, attempt_id: str, user: CurrentUser = Depends(get_current_user)
) -> QuizAttemptResponse:
    return QuizAttemptResponse(
        attempt_id=attempt_id,
        quiz_id=quiz_id,
        correct=True,
        correct_answer="1",
        xp_earned=10,
        submitted_at=datetime.now(timezone.utc),
    )
