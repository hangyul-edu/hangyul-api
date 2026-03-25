from __future__ import annotations

from src.modules.users.domain.entities import LearningProfile
from src.modules.users.domain.repositories import UserProfileRepository


class InMemoryUserProfileRepository(UserProfileRepository):
    def __init__(self) -> None:
        self._store: dict[str, LearningProfile] = {}

    def get_or_create(self, user_id: str) -> LearningProfile:
        if user_id not in self._store:
            self._store[user_id] = LearningProfile(user_id=user_id)
        return self._store[user_id]

    def save(self, profile: LearningProfile) -> LearningProfile:
        self._store[profile.user_id] = profile
        return profile
