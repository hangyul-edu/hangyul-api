from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.notifications.presentation.schemas import (
    NotificationSettings,
    NotificationsResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationsResponse, summary="List notifications for current user")
def list_notifications(
    cursor: str | None = None,
    limit: int = Query(30, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> NotificationsResponse:
    return NotificationsResponse(items=[], unread_count=0)


@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark a notification as read",
)
def mark_read(notification_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT, summary="Mark all notifications as read")
def mark_all_read(user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@router.get("/settings", response_model=NotificationSettings, summary="Get notification preferences")
def get_settings(user: CurrentUser = Depends(get_current_user)) -> NotificationSettings:
    return NotificationSettings()


@router.put("/settings", response_model=NotificationSettings, summary="Update notification preferences")
def update_settings(
    payload: NotificationSettings, user: CurrentUser = Depends(get_current_user)
) -> NotificationSettings:
    return payload
