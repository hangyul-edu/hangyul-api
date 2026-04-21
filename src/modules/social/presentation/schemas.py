from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FriendRequestStatus = Literal["pending", "accepted", "declined", "canceled"]
FeedItemType = Literal["level_up", "streak", "badge", "league_promotion", "friend_join"]


class Friend(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str | None = None
    friend_code: str
    tier: str | None = None
    points: int = 0
    last_active_at: datetime | None = None


class FriendsResponse(BaseModel):
    items: list[Friend]
    total: int


class AddFriendRequest(BaseModel):
    friend_code: str | None = Field(default=None, description="Friend code shared out-of-band")
    user_id: str | None = None


class FriendRequest(BaseModel):
    request_id: str
    from_user: Friend
    to_user: Friend
    status: FriendRequestStatus
    created_at: datetime


class FriendRequestsResponse(BaseModel):
    incoming: list[FriendRequest]
    outgoing: list[FriendRequest]


class FeedItem(BaseModel):
    feed_id: str
    type: FeedItemType
    actor: Friend
    headline: str
    description: str | None = None
    created_at: datetime
    reactions: dict[str, int] = Field(default_factory=dict)


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None


class ReactionRequest(BaseModel):
    emoji: str = Field(min_length=1, max_length=8)
