from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.writing.presentation.schemas import (
    WritingPrompt,
    WritingPromptsResponse,
    WritingSubmission,
    WritingSubmissionRequest,
    WritingSubmissionsResponse,
)

router = APIRouter(prefix="/writing", tags=["writing"])


@router.get("/prompts", response_model=WritingPromptsResponse, summary="List writing prompts")
def list_prompts(
    level: int | None = Query(None, ge=1, le=10),
    user: CurrentUser = Depends(get_current_user),
) -> WritingPromptsResponse:
    return WritingPromptsResponse(items=[])


@router.post(
    "/prompts/{prompt_id}/submissions",
    response_model=WritingSubmission,
    status_code=status.HTTP_201_CREATED,
    summary="Submit writing practice",
)
def submit_writing(
    prompt_id: str,
    payload: WritingSubmissionRequest,
    user: CurrentUser = Depends(get_current_user),
) -> WritingSubmission:
    return WritingSubmission(
        submission_id=f"wsb_{uuid4().hex[:12]}",
        prompt_id=prompt_id,
        text=payload.text,
        status="pending",
        submitted_at=datetime.now(timezone.utc),
    )


@router.get("/submissions/me", response_model=WritingSubmissionsResponse, summary="My writing submissions")
def list_my_submissions(user: CurrentUser = Depends(get_current_user)) -> WritingSubmissionsResponse:
    return WritingSubmissionsResponse(items=[])


@router.get("/submissions/{submission_id}", response_model=WritingSubmission, summary="Get submission feedback")
def get_submission(submission_id: str, user: CurrentUser = Depends(get_current_user)) -> WritingSubmission:
    return WritingSubmission(
        submission_id=submission_id,
        prompt_id="prm_123",
        text="",
        status="pending",
        submitted_at=datetime.now(timezone.utc),
    )
