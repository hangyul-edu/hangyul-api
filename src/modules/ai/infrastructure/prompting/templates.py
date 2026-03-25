from src.modules.recommendations.domain.entities import RecommendationRequest


def build_generation_prompt(request: RecommendationRequest) -> str:
    return (
        f"Situation: {request.situation}\n"
        f"Grammar: {request.grammar_focus.value}\n"
        f"Level: {request.target_level.name if request.target_level else 'auto'}\n"
        f"Mode: {request.mode.value}\n"
        f"Previous sentence: {request.previous_sentence or '-'}"
    )
