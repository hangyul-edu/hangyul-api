from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.recommendations.infrastructure.container import AppContainer, get_container
from src.common.api.membership import MembershipSummary
from src.common.exceptions import NotFoundError
from src.modules.users.presentation.schemas import (
    AvatarResponse,
    DefaultAvatar,
    DefaultAvatarsResponse,
    FeedbackRequest,
    FeedbackResponse,
    MeResponse,
    NicknameCheckRequest,
    NicknameCheckResponse,
    SelectDefaultAvatarRequest,
    UpdateMeRequest,
    UserProfileResponse,
    UserSearchResult,
)


_DEFAULT_AVATARS: dict[str, DefaultAvatar] = {
    "dav_tangerine_01": DefaultAvatar(
        default_avatar_id="dav_tangerine_01",
        name="Classic 한귤",
        image_url="https://cdn.example.com/avatars/defaults/tangerine_01.png",
        order=1,
    ),
    "dav_tangerine_02": DefaultAvatar(
        default_avatar_id="dav_tangerine_02",
        name="Book 한귤",
        image_url="https://cdn.example.com/avatars/defaults/tangerine_02.png",
        order=2,
    ),
    "dav_tangerine_03": DefaultAvatar(
        default_avatar_id="dav_tangerine_03",
        name="Graduation 한귤",
        image_url="https://cdn.example.com/avatars/defaults/tangerine_03.png",
        order=3,
    ),
}

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
        membership=MembershipSummary(tier="free", is_premium=False, expires_at=None),
        created_at=datetime.now(timezone.utc),
    )


@router.patch("/me", response_model=MeResponse, summary="Update authenticated user profile")
def update_me(payload: UpdateMeRequest, user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    return get_me(user)


@router.get(
    "/avatars/defaults",
    response_model=DefaultAvatarsResponse,
    summary="List the built-in default character avatars",
)
def list_default_avatars(user: CurrentUser = Depends(get_current_user)) -> DefaultAvatarsResponse:
    items = sorted(_DEFAULT_AVATARS.values(), key=lambda a: a.order)
    return DefaultAvatarsResponse(items=items)


@router.post(
    "/me/avatar",
    response_model=AvatarResponse,
    summary="Upload a photo from the user's device as their profile avatar",
    description="Multipart upload. Accepts a single image file (JPEG/PNG/WebP/HEIC, ≤ 5 MB).",
)
def upload_avatar(
    file: UploadFile = File(..., description="Image file taken from the phone's camera or photo library."),
    user: CurrentUser = Depends(get_current_user),
) -> AvatarResponse:
    return AvatarResponse(
        avatar_url=f"https://cdn.example.com/avatars/{user.user_id}.png",
        source="uploaded",
        default_avatar_id=None,
    )


@router.post(
    "/me/avatar/default",
    response_model=AvatarResponse,
    summary="Pick one of the default character avatars as the profile image",
)
def select_default_avatar(
    payload: SelectDefaultAvatarRequest,
    user: CurrentUser = Depends(get_current_user),
) -> AvatarResponse:
    default = _DEFAULT_AVATARS.get(payload.default_avatar_id)
    if not default:
        raise NotFoundError(f"Unknown default_avatar_id '{payload.default_avatar_id}'.")
    return AvatarResponse(
        avatar_url=default.image_url,
        source="default",
        default_avatar_id=default.default_avatar_id,
    )


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
