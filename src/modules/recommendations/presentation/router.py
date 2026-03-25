from fastapi import APIRouter, Depends

from src.modules.recommendations.domain.entities import RecommendationRequest
from src.modules.recommendations.domain.value_objects import GrammarFocus, RecommendationMode
from src.modules.recommendations.infrastructure.container import AppContainer, get_container
from src.modules.recommendations.presentation.schemas import (
    RecommendationRequestSchema,
    RecommendationResponseSchema,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponseSchema)
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
