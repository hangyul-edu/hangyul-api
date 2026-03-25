from functools import lru_cache

from src.modules.ai.infrastructure.llm.mock_generator import MockSentenceGenerator
from src.modules.recommendations.application.services import RecommendationService
from src.modules.users.application.services import UserProgressService
from src.modules.users.infrastructure.repositories import InMemoryUserProfileRepository


class AppContainer:
    def __init__(self) -> None:
        self.user_repository = InMemoryUserProfileRepository()
        self.sentence_generator = MockSentenceGenerator()
        self.recommendation_service = RecommendationService(self.sentence_generator, self.user_repository)
        self.user_progress_service = UserProgressService(self.user_repository)


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    return AppContainer()
