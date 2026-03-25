from __future__ import annotations

from dataclasses import dataclass

from src.modules.users.domain.entities import LearningProfile, ProficiencyLevel
from src.modules.users.domain.repositories import UserProfileRepository


@dataclass(slots=True)
class ProgressDecision:
    previous_level: ProficiencyLevel
    new_level: ProficiencyLevel
    reason: str


class UserProgressService:
    def __init__(self, repository: UserProfileRepository) -> None:
        self._repository = repository

    def get_profile(self, user_id: str) -> LearningProfile:
        return self._repository.get_or_create(user_id)

    def apply_feedback(self, user_id: str, was_helpful: bool, requested_direction: str | None = None) -> ProgressDecision:
        profile = self._repository.get_or_create(user_id)
        previous_level = profile.level

        if was_helpful:
            profile.record_success()
            if requested_direction == "harder" or profile.streak >= 3:
                profile.level = profile.level.harder()
                reason = "성공 피드백과 학습 흐름을 반영해 난이도를 올렸습니다."
            else:
                reason = "현재 수준을 유지하면서 같은 난이도로 학습을 이어갑니다."
        else:
            profile.record_failure()
            if requested_direction == "easier" or profile.unsuccessful_answers >= 2:
                profile.level = profile.level.easier()
                reason = "부담을 줄이기 위해 더 쉬운 수준으로 조정했습니다."
            else:
                reason = "같은 수준에서 다른 방식의 문장을 제안합니다."

        self._repository.save(profile)
        return ProgressDecision(previous_level=previous_level, new_level=profile.level, reason=reason)
