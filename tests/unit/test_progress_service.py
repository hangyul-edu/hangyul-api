from src.modules.users.application.services import UserProgressService
from src.modules.users.infrastructure.repositories import InMemoryUserProfileRepository


def test_level_goes_up_after_streak() -> None:
    repository = InMemoryUserProfileRepository()
    service = UserProgressService(repository)
    user_id = "u1"

    service.apply_feedback(user_id, True, None)
    service.apply_feedback(user_id, True, None)
    decision = service.apply_feedback(user_id, True, None)

    assert decision.previous_level.name == "BEGINNER_1"
    assert decision.new_level.name == "BEGINNER_2"
