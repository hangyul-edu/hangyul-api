from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

NotificationCategory = Literal[
    "learning_reminder", "streak", "friend", "league", "announcement", "marketing", "system"
]


class Notification(BaseModel):
    notification_id: str
    category: NotificationCategory
    title: str
    body: str | None = None
    image_url: str | None = None
    deep_link: str | None = None
    read: bool = False
    created_at: datetime


class NotificationsResponse(BaseModel):
    items: list[Notification]
    unread_count: int
    next_cursor: str | None = None


class NotificationSettings(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = True
    learning_reminder: bool = True
    daily_reminder_time: str | None = None
    streak_alerts: bool = True
    friend_alerts: bool = True
    league_alerts: bool = True
    marketing: bool = False
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
