from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.social.presentation.schemas import (
    AddFriendRequest,
    FeedResponse,
    FriendRequest,
    FriendRequestsResponse,
    FriendsResponse,
    ReactionRequest,
)

friends_router = APIRouter(prefix="/friends", tags=["social"])
feed_router = APIRouter(prefix="/feed", tags=["social"])


@friends_router.get("", response_model=FriendsResponse, summary="List my friends")
def list_friends(user: CurrentUser = Depends(get_current_user)) -> FriendsResponse:
    return FriendsResponse(items=[], total=0)


@friends_router.post(
    "",
    response_model=FriendRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Send a friend request",
)
def send_friend_request(payload: AddFriendRequest, user: CurrentUser = Depends(get_current_user)) -> FriendRequest:
    raise NotImplementedError


@friends_router.delete(
    "/{friend_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a friend",
)
def remove_friend(friend_user_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@friends_router.get("/requests", response_model=FriendRequestsResponse, summary="List friend requests")
def list_friend_requests(user: CurrentUser = Depends(get_current_user)) -> FriendRequestsResponse:
    return FriendRequestsResponse(incoming=[], outgoing=[])


@friends_router.post(
    "/requests/{request_id}/accept",
    response_model=FriendRequest,
    summary="Accept a friend request",
)
def accept_friend_request(request_id: str, user: CurrentUser = Depends(get_current_user)) -> FriendRequest:
    raise NotImplementedError


@friends_router.post(
    "/requests/{request_id}/decline",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Decline a friend request",
)
def decline_friend_request(request_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@feed_router.get("", response_model=FeedResponse, summary="Activity feed from friends & me")
def get_feed(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> FeedResponse:
    return FeedResponse(items=[])


@feed_router.post(
    "/{feed_id}/reactions",
    status_code=status.HTTP_201_CREATED,
    summary="React to a feed item",
)
def react_to_feed(
    feed_id: str, payload: ReactionRequest, user: CurrentUser = Depends(get_current_user)
) -> dict[str, str]:
    return {"feed_id": feed_id, "emoji": payload.emoji}
