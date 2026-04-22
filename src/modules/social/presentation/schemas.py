from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FeedItemType = Literal["level_up", "streak", "badge", "league_promotion", "friend_join"]


class SocialUser(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str | None = None
    friend_code: str
    tier: str | None = None
    points: int = 0
    last_active_at: datetime | None = None
    is_following: bool = Field(description="True if the caller follows this user.")
    follows_me: bool = Field(description="True if this user follows the caller.")


class ConnectionsResponse(BaseModel):
    following: list[SocialUser] = Field(description="People the caller is following.")
    following_count: int = Field(ge=0)
    followers: list[SocialUser] = Field(description="People who follow the caller.")
    followers_count: int = Field(ge=0)


class ContactMatchesResponse(BaseModel):
    items: list[SocialUser] = Field(
        description=(
            "Hangyul users found in the caller's phone address book. Each entry carries "
            "is_following / follows_me so the UI can label the action button as 'Follow' or "
            "'Follow back' and hide users the caller already follows."
        )
    )


class FollowResponse(BaseModel):
    user_id: str
    is_following: bool
    follows_me: bool


class FeedItem(BaseModel):
    feed_id: str
    type: FeedItemType
    actor: SocialUser
    headline: str
    description: str | None = None
    created_at: datetime
    reactions: dict[str, int] = Field(default_factory=dict)


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None


class ReactionRequest(BaseModel):
    emoji: str = Field(min_length=1, max_length=8)
