from __future__ import annotations

from abc import ABC, abstractmethod

from src.modules.recommendations.domain.entities import RecommendationRequest, RecommendationResult


class SentenceGenerationPort(ABC):
    @abstractmethod
    def generate(self, request: RecommendationRequest) -> RecommendationResult:
        raise NotImplementedError
