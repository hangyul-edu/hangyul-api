from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.announcements.presentation.schemas import (
    Announcement,
    AnnouncementsResponse,
)

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=AnnouncementsResponse, summary="List announcements")
def list_announcements(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
) -> AnnouncementsResponse:
    return AnnouncementsResponse(items=[])


@router.get("/{announcement_id}", response_model=Announcement, summary="Get announcement detail")
def get_announcement(announcement_id: str, user: CurrentUser = Depends(get_current_user)) -> Announcement:
    return Announcement(
        announcement_id=announcement_id,
        title="안내",
        body="자세한 내용은 앱 내 공지사항을 참고해주세요.",
        category="notice",
        published_at=datetime.now(timezone.utc),
    )
