from pydantic import BaseModel


class RecommendationRequestSchema(BaseModel):
    user_id: str
    situation: str
    grammar_focus: str
    mode: str = "fresh"
    previous_sentence: str | None = None


class RecommendationResponseSchema(BaseModel):
    sentence: str
    translation: str
    grammar_focus: str
    target_level: str
    explanation: str
    next_suggestions: list[str]
