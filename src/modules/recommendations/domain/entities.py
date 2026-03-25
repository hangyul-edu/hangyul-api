from __future__ import annotations

from dataclasses import dataclass

from src.modules.recommendations.domain.value_objects import GrammarFocus, RecommendationMode
from src.modules.users.domain.entities import ProficiencyLevel


@dataclass(slots=True)
class RecommendationRequest:
    user_id: str
    situation: str
    grammar_focus: GrammarFocus
    mode: RecommendationMode = RecommendationMode.FRESH
    target_level: ProficiencyLevel | None = None
    previous_sentence: str | None = None


@dataclass(slots=True)
class RecommendationResult:
    sentence: str
    translation: str
    grammar_focus: GrammarFocus
    target_level: ProficiencyLevel
    explanation: str
    next_suggestions: list[str]
