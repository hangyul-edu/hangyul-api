from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.onboarding.presentation.schemas import (
    OnboardingOption,
    OnboardingQuestion,
    OnboardingQuestionsResponse,
    OnboardingStatusResponse,
    OnboardingSubmissionRequest,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/questions", response_model=OnboardingQuestionsResponse, summary="Get onboarding question set")
def get_questions() -> OnboardingQuestionsResponse:
    return OnboardingQuestionsResponse(
        questions=[
            OnboardingQuestion(
                key="purpose",
                prompt="무엇을 위해 한국어를 배우시나요?",
                options=[
                    OnboardingOption(code="conversation", label="일상 회화"),
                    OnboardingOption(code="topik", label="TOPIK 시험"),
                ],
            ),
            OnboardingQuestion(
                key="speaking_level",
                prompt="현재 회화 수준은 어느 정도인가요?",
                options=[
                    OnboardingOption(code="beginner", label="초급"),
                    OnboardingOption(code="elementary", label="초중급"),
                    OnboardingOption(code="intermediate", label="중급"),
                    OnboardingOption(code="advanced", label="고급"),
                    OnboardingOption(code="fluent", label="유창"),
                ],
            ),
            OnboardingQuestion(
                key="topik_target",
                prompt="목표 TOPIK 등급",
                options=[OnboardingOption(code=str(i), label=f"{i}급") for i in range(1, 7)]
                + [OnboardingOption(code="none", label="해당 없음")],
            ),
        ]
    )


@router.post(
    "/responses",
    response_model=OnboardingStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit onboarding answers",
)
def submit_responses(
    payload: OnboardingSubmissionRequest, user: CurrentUser = Depends(get_current_user)
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse(
        completed=True,
        purpose=payload.purpose,
        speaking_level=payload.speaking_level,
        topik_target=payload.topik_target,
        recommended_track_id="trk_topik_intermediate",
        recommended_level=3,
    )


@router.get("/status", response_model=OnboardingStatusResponse, summary="Get onboarding status")
def get_status(user: CurrentUser = Depends(get_current_user)) -> OnboardingStatusResponse:
    return OnboardingStatusResponse(completed=False)
