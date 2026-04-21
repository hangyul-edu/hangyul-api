from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AnnouncementCategory = Literal["notice", "event", "update", "maintenance"]


class Announcement(BaseModel):
    announcement_id: str
    title: str
    body: str
    category: AnnouncementCategory
    pinned: bool = False
    published_at: datetime
    cover_image_url: str | None = None


class AnnouncementsResponse(BaseModel):
    items: list[Announcement]
    next_cursor: str | None = None
