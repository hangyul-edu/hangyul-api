from __future__ import annotations

from src.modules.ai.domain.ports import SentenceGenerationPort
from src.modules.recommendations.domain.entities import RecommendationRequest, RecommendationResult
from src.modules.recommendations.domain.value_objects import RecommendationMode
from src.modules.users.domain.entities import ProficiencyLevel
from src.modules.users.domain.repositories import UserProfileRepository


class RecommendationService:
    def __init__(self, generator: SentenceGenerationPort, user_repository: UserProfileRepository) -> None:
        self._generator = generator
        self._user_repository = user_repository

    def recommend(self, request: RecommendationRequest) -> RecommendationResult:
        profile = self._user_repository.get_or_create(request.user_id)
        target_level = request.target_level or profile.level

        if request.mode == RecommendationMode.HARDER:
            target_level = target_level.harder()
        elif request.mode == RecommendationMode.EASIER:
            target_level = target_level.easier()

        enriched_request = RecommendationRequest(
            user_id=request.user_id,
            situation=request.situation,
            grammar_focus=request.grammar_focus,
            mode=request.mode,
            target_level=target_level,
            previous_sentence=request.previous_sentence,
        )
        return self._generator.generate(enriched_request)
