from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    user_id: str
    level: str
    streak: int
    successful_answers: int
    unsuccessful_answers: int


class FeedbackRequest(BaseModel):
    user_id: str
    was_helpful: bool
    requested_direction: str | None = None


class FeedbackResponse(BaseModel):
    previous_level: str
    new_level: str
    reason: str
