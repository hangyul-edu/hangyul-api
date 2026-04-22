from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.social.presentation.schemas import (
    ConnectionsResponse,
    ContactMatchesResponse,
    FeedResponse,
    FollowResponse,
    ReactionRequest,
)

friends_router = APIRouter(prefix="/friends", tags=["social"])
feed_router = APIRouter(prefix="/feed", tags=["social"])


@friends_router.get(
    "/connections",
    response_model=ConnectionsResponse,
    summary="Followers and following lists for the friend management page",
    description=(
        "Single call that powers the friend management page. Returns both lists plus counts. "
        "Every entry carries `is_following` (the caller follows them) and `follows_me` (they "
        "follow the caller) so the UI can label buttons as 'Follow', 'Follow back', 'Following', "
        "or 'Remove' without additional lookups."
    ),
)
def get_connections(user: CurrentUser = Depends(get_current_user)) -> ConnectionsResponse:
    return ConnectionsResponse(following=[], following_count=0, followers=[], followers_count=0)


@friends_router.get(
    "/contact-matches",
    response_model=ContactMatchesResponse,
    summary="Hangyul users found in the caller's phone contacts",
    description=(
        "Requires `settings.contact_access_granted == true` (see §4.17). When consent is missing, "
        "the server responds with `403 forbidden` and a `contact-access required` detail. Each "
        "match carries is_following / follows_me so the client can show 'Follow' or "
        "'Follow back' next to each person."
    ),
)
def list_contact_matches(user: CurrentUser = Depends(get_current_user)) -> ContactMatchesResponse:
    return ContactMatchesResponse(items=[])


@friends_router.post(
    "/{user_id}/follow",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Follow a user (also used for 'Follow back')",
    description=(
        "Creates a directed edge from the caller to `user_id`. Same endpoint is used for the "
        "initial follow and for follow-back (when the target already follows the caller). "
        "Idempotent — calling twice simply returns the current state."
    ),
)
def follow_user(user_id: str, user: CurrentUser = Depends(get_current_user)) -> FollowResponse:
    return FollowResponse(user_id=user_id, is_following=True, follows_me=False)


@friends_router.delete(
    "/{user_id}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a connection — an unfollow toward the other user",
    description=(
        "Removes the caller → `user_id` follow edge. Does not affect the opposite edge: if "
        "`user_id` follows the caller, that relationship is unchanged. Idempotent `204` even if "
        "the caller was not following the user."
    ),
)
def unfollow_user(user_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@feed_router.get("", response_model=FeedResponse, summary="Activity feed from people the caller follows")
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
