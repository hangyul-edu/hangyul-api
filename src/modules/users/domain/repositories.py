from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import LearningProfile


class UserProfileRepository(ABC):
    @abstractmethod
    def get_or_create(self, user_id: str) -> LearningProfile:
        raise NotImplementedError

    @abstractmethod
    def save(self, profile: LearningProfile) -> LearningProfile:
        raise NotImplementedError
