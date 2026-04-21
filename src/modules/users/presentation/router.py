from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.recommendations.infrastructure.container import AppContainer, get_container
from src.modules.users.presentation.schemas import (
    AvatarUploadResponse,
    FeedbackRequest,
    FeedbackResponse,
    MeResponse,
    NicknameCheckRequest,
    NicknameCheckResponse,
    UpdateMeRequest,
    UserProfileResponse,
    UserSearchResult,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeResponse, summary="Get authenticated user profile")
def get_me(user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user_id=user.user_id,
        email="student@example.com",
        nickname="한글러",
        avatar_url=None,
        phone_verified=True,
        language="ko",
        learning_language="ko",
        tier="green",
        points=0,
        streak_days=0,
        subscription_active=False,
        created_at=datetime.now(timezone.utc),
    )


@router.patch("/me", response_model=MeResponse, summary="Update authenticated user profile")
def update_me(payload: UpdateMeRequest, user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    return get_me(user)


@router.post(
    "/me/avatar",
    response_model=AvatarUploadResponse,
    summary="Upload profile avatar image",
)
def upload_avatar(file: UploadFile = File(...), user: CurrentUser = Depends(get_current_user)) -> AvatarUploadResponse:
    return AvatarUploadResponse(avatar_url=f"https://cdn.example.com/avatars/{user.user_id}.png")


@router.post(
    "/check-nickname",
    response_model=NicknameCheckResponse,
    summary="Check whether a nickname is available",
)
def check_nickname(payload: NicknameCheckRequest) -> NicknameCheckResponse:
    return NicknameCheckResponse(nickname=payload.nickname, available=True)


@router.get(
    "/search",
    response_model=list[UserSearchResult],
    summary="Search users by friend code or nickname",
)
def search_users(code: str | None = None, nickname: str | None = None, user: CurrentUser = Depends(get_current_user)) -> list[UserSearchResult]:
    return []


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
