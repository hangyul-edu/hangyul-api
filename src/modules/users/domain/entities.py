from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class ProficiencyLevel(IntEnum):
    BEGINNER_1 = 1
    BEGINNER_2 = 2
    BEGINNER_3 = 3
    INTERMEDIATE_1 = 4
    INTERMEDIATE_2 = 5
    ADVANCED_1 = 6

    def harder(self) -> "ProficiencyLevel":
        return ProficiencyLevel(min(self.value + 1, max(level.value for level in ProficiencyLevel)))

    def easier(self) -> "ProficiencyLevel":
        return ProficiencyLevel(max(self.value - 1, min(level.value for level in ProficiencyLevel)))


@dataclass(slots=True)
class LearningProfile:
    user_id: str
    level: ProficiencyLevel = ProficiencyLevel.BEGINNER_1
    streak: int = 0
    successful_answers: int = 0
    unsuccessful_answers: int = 0
    preferred_topics: list[str] = field(default_factory=list)

    def record_success(self) -> None:
        self.successful_answers += 1
        self.streak += 1

    def record_failure(self) -> None:
        self.unsuccessful_answers += 1
        self.streak = 0
