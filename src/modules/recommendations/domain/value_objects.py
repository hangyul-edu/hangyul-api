from enum import StrEnum


class GrammarFocus(StrEnum):
    POLITE_PRESENT = "polite_present"
    PAST = "past"
    FUTURE = "future"
    HONORIFIC = "honorific"
    CAUSAL = "causal"
    CONTRAST = "contrast"


class RecommendationMode(StrEnum):
    FRESH = "fresh"
    SIMILAR = "similar"
    DIFFERENT_GRAMMAR = "different_grammar"
    HARDER = "harder"
    EASIER = "easier"
