from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

UiLanguage = Literal["ko", "en", "ja", "zh-CN", "zh-TW", "vi", "th", "id"]
AppTheme = Literal["system", "light", "dark"]
DailyItemGoal = Literal[5, 10, 20, 30, 40]


class AppSettings(BaseModel):
    language: UiLanguage = "ko"
    theme: AppTheme = "system"
    sound_effects: bool = True
    vibration: bool = True
    autoplay_audio: bool = True
    show_romanization: bool = True
    exclude_speaking: bool = Field(
        default=False,
        description=(
            "Lesson-screen 'Exclude Speaking' toggle. When true, clients suppress in-lecture popups "
            "with kind == 'conversation_speak' (see §4.6); topik_question popups still fire. "
            "Useful when the user cannot speak aloud (commute, office, etc.). Defaults to off."
        ),
    )
    daily_sentence_goal: DailyItemGoal = Field(
        default=10,
        description=(
            "Daily milestone for Conversation sentences studied today. Chosen from the fixed set "
            "5 / 10 / 20 / 30 / 40. Users may study beyond this count; the value is only used to "
            "decide whether the daily goal has been met."
        ),
    )
    daily_question_goal: DailyItemGoal = Field(
        default=10,
        description=(
            "Daily milestone for TOPIK questions attempted today. Chosen from the fixed set "
            "5 / 10 / 20 / 30 / 40. Users may attempt more; overflow does not change goal status."
        ),
    )


class UpdateAppSettingsRequest(BaseModel):
    language: UiLanguage | None = None
    theme: AppTheme | None = None
    sound_effects: bool | None = None
    vibration: bool | None = None
    autoplay_audio: bool | None = None
    show_romanization: bool | None = None
    exclude_speaking: bool | None = None
    daily_sentence_goal: DailyItemGoal | None = None
    daily_question_goal: DailyItemGoal | None = None
