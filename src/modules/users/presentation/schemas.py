from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserProfileResponse(BaseModel):
    user_id: str
    level: str
    streak: int
    successful_answers: int
    unsuccessful_answers: int


class FeedbackRequest(BaseModel):
    user_id: str
    was_helpful: bool
    requested_direction: str | None = None


class FeedbackResponse(BaseModel):
    previous_level: str
    new_level: str
    reason: str


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    nickname: str
    avatar_url: str | None = None
    avatar_source: Literal["uploaded", "default", "none"] = Field(
        default="none",
        description="How `avatar_url` was set: uploaded photo, picked default character, or not set yet.",
    )
    default_avatar_id: str | None = Field(
        default=None,
        description="Populated when avatar_source == 'default'; references the picked DefaultAvatar.",
    )
    phone_verified: bool = False
    language: str = Field(default="ko", description="BCP-47 code for UI language")
    learning_language: str = "ko"
    tier: str = Field(default="green", description="Current league tier")
    points: int = 0
    streak_days: int = 0
    subscription_active: bool = False
    created_at: datetime


class UpdateMeRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=20)
    avatar_url: str | None = None
    language: Literal["ko", "en", "ja", "zh-CN", "zh-TW", "vi", "th", "id"] | None = None


class NicknameCheckRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=20)


class NicknameCheckResponse(BaseModel):
    nickname: str
    available: bool


AvatarSource = Literal["uploaded", "default"]


class AvatarResponse(BaseModel):
    avatar_url: str
    source: AvatarSource = Field(description="How the current avatar was chosen.")
    default_avatar_id: str | None = Field(
        default=None,
        description="Populated when `source == 'default'`; references the picked DefaultAvatar.",
    )


class DefaultAvatar(BaseModel):
    default_avatar_id: str = Field(description="Stable catalog id, e.g. 'dav_tangerine_01'.")
    name: str = Field(description="Human-readable label shown under the tile.")
    image_url: str = Field(description="CDN URL of the character image.")
    order: int = 0


class DefaultAvatarsResponse(BaseModel):
    items: list[DefaultAvatar]


class SelectDefaultAvatarRequest(BaseModel):
    default_avatar_id: str


class UserSearchResult(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str | None = None
    friend_code: str
