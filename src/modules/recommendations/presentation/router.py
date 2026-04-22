from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.recommendations.domain.entities import RecommendationRequest
from src.modules.recommendations.domain.value_objects import GrammarFocus, RecommendationMode
from src.modules.recommendations.infrastructure.container import AppContainer, get_container
from src.modules.recommendations.presentation.schemas import (
    QuestionRecommendationRequest,
    QuestionRecommendationResponse,
    RecommendationHistoryResponse,
    RecommendationRequestSchema,
    RecommendationResponseSchema,
    SentenceRecommendationRequest,
    SentenceRecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponseSchema, summary="Legacy internal recommender")
def create_recommendation(
    payload: RecommendationRequestSchema,
    container: AppContainer = Depends(get_container),
) -> RecommendationResponseSchema:
    result = container.recommendation_service.recommend(
        RecommendationRequest(
            user_id=payload.user_id,
            situation=payload.situation,
            grammar_focus=GrammarFocus(payload.grammar_focus),
            mode=RecommendationMode(payload.mode),
            previous_sentence=payload.previous_sentence,
        )
    )
    return RecommendationResponseSchema(
        sentence=result.sentence,
        translation=result.translation,
        grammar_focus=result.grammar_focus.value,
        target_level=result.target_level.name,
        explanation=result.explanation,
        next_suggestions=result.next_suggestions,
    )


@router.post(
    "/sentences",
    response_model=SentenceRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Recommend Conversation-track sentences (level-based or prompt-driven)",
)
def recommend_sentences(
    payload: SentenceRecommendationRequest,
    user: CurrentUser = Depends(get_current_user),
) -> SentenceRecommendationResponse:
    level = payload.level if payload.level is not None else 1
    return SentenceRecommendationResponse(level=level, prompt=payload.prompt, items=[])


@router.post(
    "/questions",
    response_model=QuestionRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Recommend TOPIK-track questions (level-based or prompt-driven)",
)
def recommend_questions(
    payload: QuestionRecommendationRequest,
    user: CurrentUser = Depends(get_current_user),
) -> QuestionRecommendationResponse:
    level = payload.level if payload.level is not None else 1
    return QuestionRecommendationResponse(level=level, prompt=payload.prompt, items=[])


@router.get(
    "/history",
    response_model=RecommendationHistoryResponse,
    summary="Recently recommended items for the caller",
)
def get_recommendation_history(
    kind: str = Query(..., pattern="^(sentences|questions)$"),
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> RecommendationHistoryResponse:
    return RecommendationHistoryResponse(items=[])
