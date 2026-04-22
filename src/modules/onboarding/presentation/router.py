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

_DAILY_ITEM_OPTIONS = [
    OnboardingOption(code="5", label="5"),
    OnboardingOption(code="10", label="10"),
    OnboardingOption(code="20", label="20"),
    OnboardingOption(code="30", label="30"),
    OnboardingOption(code="40", label="40"),
]


@router.get(
    "/questions",
    response_model=OnboardingQuestionsResponse,
    summary="Get onboarding question set (ordered by screen flow)",
)
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
                    OnboardingOption(code="beginner", label="완전 초보", description="아직 한국어를 거의 모릅니다."),
                    OnboardingOption(code="elementary", label="단어 몇 개", description="단어 몇 개 정도 알고 있어요."),
                    OnboardingOption(
                        code="intermediate",
                        label="간단한 문장",
                        description="간단한 문장을 말할 수 있어요.",
                    ),
                    OnboardingOption(
                        code="advanced",
                        label="일상 대화",
                        description="일상적인 대화는 할 수 있어요.",
                    ),
                    OnboardingOption(code="fluent", label="유창함", description="원어민과 자연스럽게 대화할 수 있어요."),
                ],
            ),
            OnboardingQuestion(
                key="topik_target",
                prompt="목표 TOPIK 급수를 선택해 주세요 (TOPIK 목적 선택 시).",
                options=[OnboardingOption(code=str(i), label=f"{i}급") for i in range(1, 7)]
                + [OnboardingOption(code="none", label="해당 없음")],
            ),
            OnboardingQuestion(
                key="daily_sentence_goal",
                prompt="하루에 몇 개의 문장을 학습할까요? (회화 목적 선택 시)",
                options=_DAILY_ITEM_OPTIONS,
            ),
            OnboardingQuestion(
                key="daily_question_goal",
                prompt="하루에 몇 개의 TOPIK 문제를 풀까요? (TOPIK 목적 선택 시)",
                options=_DAILY_ITEM_OPTIONS,
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
    sentence_goal = payload.daily_sentence_goal if payload.purpose == "conversation" else 10
    question_goal = payload.daily_question_goal if payload.purpose == "topik" else 10
    return OnboardingStatusResponse(
        completed=True,
        purpose=payload.purpose,
        speaking_level=payload.speaking_level,
        topik_target=payload.topik_target,
        daily_sentence_goal=sentence_goal or 10,
        daily_question_goal=question_goal or 10,
        recommended_track_id="trk_topik" if payload.purpose == "topik" else "trk_conversation",
        recommended_level=3,
    )


@router.get("/status", response_model=OnboardingStatusResponse, summary="Get onboarding status")
def get_status(user: CurrentUser = Depends(get_current_user)) -> OnboardingStatusResponse:
    return OnboardingStatusResponse(completed=False)
