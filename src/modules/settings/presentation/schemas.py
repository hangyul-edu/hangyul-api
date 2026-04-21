from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

UiLanguage = Literal["ko", "en", "ja", "zh-CN", "zh-TW", "vi", "th", "id"]
AppTheme = Literal["system", "light", "dark"]


class AppSettings(BaseModel):
    language: UiLanguage = "ko"
    theme: AppTheme = "system"
    sound_effects: bool = True
    vibration: bool = True
    autoplay_audio: bool = True
    show_romanization: bool = True
    daily_goal_minutes: int = 10


class UpdateAppSettingsRequest(BaseModel):
    language: UiLanguage | None = None
    theme: AppTheme | None = None
    sound_effects: bool | None = None
    vibration: bool | None = None
    autoplay_audio: bool | None = None
    show_romanization: bool | None = None
    daily_goal_minutes: int | None = None
