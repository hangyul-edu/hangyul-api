from fastapi import APIRouter, Depends

from src.modules.recommendations.infrastructure.container import AppContainer, get_container
from src.modules.users.presentation.schemas import FeedbackRequest, FeedbackResponse, UserProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
def get_profile(user_id: str, container: AppContainer = Depends(get_container)) -> UserProfileResponse:
    profile = container.user_progress_service.get_profile(user_id)
    return UserProfileResponse(
        user_id=profile.user_id,
        level=profile.level.name,
        streak=profile.streak,
        successful_answers=profile.successful_answers,
        unsuccessful_answers=profile.unsuccessful_answers,
    )


@router.post("/feedback", response_model=FeedbackResponse)
def apply_feedback(payload: FeedbackRequest, container: AppContainer = Depends(get_container)) -> FeedbackResponse:
    decision = container.user_progress_service.apply_feedback(
        user_id=payload.user_id,
        was_helpful=payload.was_helpful,
        requested_direction=payload.requested_direction,
    )
    return FeedbackResponse(
        previous_level=decision.previous_level.name,
        new_level=decision.new_level.name,
        reason=decision.reason,
    )
