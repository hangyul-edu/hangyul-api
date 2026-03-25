from __future__ import annotations

from collections import defaultdict

from src.modules.ai.domain.ports import SentenceGenerationPort
from src.modules.recommendations.domain.entities import RecommendationRequest, RecommendationResult
from src.modules.recommendations.domain.value_objects import GrammarFocus, RecommendationMode
from src.modules.users.domain.entities import ProficiencyLevel


class MockSentenceGenerator(SentenceGenerationPort):
    def __init__(self) -> None:
        self._corpus = self._build_corpus()
        self._index = defaultdict(int)

    def generate(self, request: RecommendationRequest) -> RecommendationResult:
        level = request.target_level or ProficiencyLevel.BEGINNER_1
        grammar = request.grammar_focus

        if request.mode == RecommendationMode.DIFFERENT_GRAMMAR:
            grammar = self._alternate_grammar(grammar)
        elif request.mode == RecommendationMode.HARDER:
            level = level.harder()
        elif request.mode == RecommendationMode.EASIER:
            level = level.easier()

        options = self._corpus.get(request.situation, self._corpus["daily_life"])
        pool = options.get(level, options[ProficiencyLevel.BEGINNER_1])
        entries = pool.get(grammar, next(iter(pool.values())))

        idx_key = f"{request.situation}:{level.value}:{grammar.value}:{request.mode.value}"
        entry = entries[self._index[idx_key] % len(entries)]
        self._index[idx_key] += 1

        explanation = self._build_explanation(request.mode, level, grammar)
        return RecommendationResult(
            sentence=entry["sentence"],
            translation=entry["translation"],
            grammar_focus=grammar,
            target_level=level,
            explanation=explanation,
            next_suggestions=["similar", "different_grammar", "harder", "easier"],
        )

    def _alternate_grammar(self, grammar: GrammarFocus) -> GrammarFocus:
        ordered = list(GrammarFocus)
        idx = ordered.index(grammar)
        return ordered[(idx + 1) % len(ordered)]

    def _build_explanation(self, mode: RecommendationMode, level: ProficiencyLevel, grammar: GrammarFocus) -> str:
        mapping = {
            RecommendationMode.FRESH: "현재 상황과 수준에 맞춘 기본 추천입니다.",
            RecommendationMode.SIMILAR: "같은 상황에서 비슷한 표현을 반복 학습할 수 있게 골랐습니다.",
            RecommendationMode.DIFFERENT_GRAMMAR: "같은 상황을 다른 문법으로 표현해 보도록 바꿨습니다.",
            RecommendationMode.HARDER: "조금 더 긴 문장과 확장된 표현으로 난이도를 올렸습니다.",
            RecommendationMode.EASIER: "핵심 의미는 유지하면서 더 짧고 쉬운 문장으로 낮췄습니다.",
        }
        return f"{mapping[mode]} 목표 수준은 {level.name}이고, 문법 포인트는 {grammar.value} 입니다."

    def _build_corpus(self) -> dict[str, dict[ProficiencyLevel, dict[GrammarFocus, list[dict[str, str]]]]]:
        B1 = ProficiencyLevel.BEGINNER_1
        B2 = ProficiencyLevel.BEGINNER_2
        B3 = ProficiencyLevel.BEGINNER_3
        I1 = ProficiencyLevel.INTERMEDIATE_1
        return {
            "daily_life": {
                B1: {
                    GrammarFocus.POLITE_PRESENT: [
                        {"sentence": "오늘은 집에서 쉬어요.", "translation": "I rest at home today."},
                        {"sentence": "저는 아침에 물을 마셔요.", "translation": "I drink water in the morning."},
                    ],
                    GrammarFocus.PAST: [
                        {"sentence": "어제는 일찍 잤어요.", "translation": "I slept early yesterday."},
                    ],
                    GrammarFocus.FUTURE: [
                        {"sentence": "내일은 공원에 갈 거예요.", "translation": "I will go to the park tomorrow."},
                    ],
                    GrammarFocus.HONORIFIC: [
                        {"sentence": "할머니께서 식사하세요.", "translation": "Grandmother is having a meal."},
                    ],
                    GrammarFocus.CAUSAL: [
                        {"sentence": "비가 와서 집에 있어요.", "translation": "I stay home because it is raining."},
                    ],
                    GrammarFocus.CONTRAST: [
                        {"sentence": "커피는 좋아하지만 차는 안 마셔요.", "translation": "I like coffee, but I do not drink tea."},
                    ],
                },
                B2: {
                    GrammarFocus.POLITE_PRESENT: [
                        {"sentence": "퇴근 후에는 가볍게 산책하면서 하루를 정리해요.", "translation": "After work, I take a light walk and wind down the day."},
                    ],
                    GrammarFocus.PAST: [
                        {"sentence": "주말에는 가족과 함께 시장에 다녀왔어요.", "translation": "I went to the market with my family over the weekend."},
                    ],
                    GrammarFocus.FUTURE: [
                        {"sentence": "이번 주말에는 방을 정리하고 책도 읽을 거예요.", "translation": "This weekend, I will clean my room and read a book."},
                    ],
                    GrammarFocus.HONORIFIC: [
                        {"sentence": "선생님께서 수업 전에 자료를 나눠 주세요.", "translation": "The teacher hands out materials before class."},
                    ],
                    GrammarFocus.CAUSAL: [
                        {"sentence": "몸이 조금 피곤해서 오늘은 일찍 들어가려고 해요.", "translation": "I feel a little tired, so I plan to go home early today."},
                    ],
                    GrammarFocus.CONTRAST: [
                        {"sentence": "아침에는 바쁘지만 밤에는 비교적 여유가 있어요.", "translation": "Mornings are busy, but evenings are relatively relaxed."},
                    ],
                },
                B3: {
                    GrammarFocus.POLITE_PRESENT: [
                        {"sentence": "출근하기 전에 간단히 뉴스를 확인하고 하루 일정을 정리해요.", "translation": "Before heading to work, I check the news and organize my schedule."},
                    ],
                    GrammarFocus.PAST: [
                        {"sentence": "지난달에는 생활 패턴을 바꾸기 위해 매일 아침 운동을 했어요.", "translation": "Last month, I exercised every morning to change my routine."},
                    ],
                    GrammarFocus.FUTURE: [
                        {"sentence": "앞으로는 시간을 더 효율적으로 쓰기 위해 저녁마다 계획을 세울 거예요.", "translation": "From now on, I will plan each evening to use my time more efficiently."},
                    ],
                    GrammarFocus.HONORIFIC: [
                        {"sentence": "부장님께서 회의 전에 주요 안건을 다시 설명해 주셨어요.", "translation": "The director explained the main agenda again before the meeting."},
                    ],
                    GrammarFocus.CAUSAL: [
                        {"sentence": "잠을 충분히 못 자서 오전 내내 집중하기가 쉽지 않았어요.", "translation": "Because I did not get enough sleep, it was hard to focus all morning."},
                    ],
                    GrammarFocus.CONTRAST: [
                        {"sentence": "집에서는 조용히 쉬고 싶지만 밖에 나가면 오히려 기분이 전환돼요.", "translation": "I want to rest quietly at home, but going outside actually refreshes me."},
                    ],
                },
                I1: {
                    GrammarFocus.POLITE_PRESENT: [
                        {"sentence": "평일에는 업무 우선순위를 정한 뒤, 남는 시간에 개인 공부를 병행하려고 노력해요.", "translation": "On weekdays, I prioritize my tasks and try to combine them with personal study in my spare time."},
                    ],
                    GrammarFocus.PAST: [
                        {"sentence": "최근에는 생활 습관을 개선하려고 수면 시간과 식사 시간을 꾸준히 기록해 왔어요.", "translation": "Recently, I have been consistently recording my sleep and meal times to improve my habits."},
                    ],
                    GrammarFocus.FUTURE: [
                        {"sentence": "다음 달부터는 생산성을 높이기 위해 디지털 기기 사용 시간을 더 엄격하게 관리할 생각이에요.", "translation": "Starting next month, I plan to manage my screen time more strictly to improve productivity."},
                    ],
                    GrammarFocus.HONORIFIC: [
                        {"sentence": "원장님께서 학습 방향을 조정해 보자고 제안하시면서 구체적인 예시도 함께 들어 주셨어요.", "translation": "The director suggested adjusting the learning direction and also provided concrete examples."},
                    ],
                    GrammarFocus.CAUSAL: [
                        {"sentence": "요즘 해야 할 일이 많아서 예전보다 여가 시간을 의식적으로 확보하지 않으면 쉽게 지치게 돼요.", "translation": "These days, because I have a lot to do, I get tired easily unless I consciously make time for rest."},
                    ],
                    GrammarFocus.CONTRAST: [
                        {"sentence": "혼자 공부하면 집중은 잘되지만, 다른 사람과 함께하면 놓친 표현을 더 빨리 발견할 수 있어요.", "translation": "Studying alone helps me focus, but studying with others helps me catch missed expressions faster."},
                    ],
                },
            },
            "travel": {
                B1: {
                    GrammarFocus.POLITE_PRESENT: [{"sentence": "여행 가면 사진을 많이 찍어요.", "translation": "When I travel, I take many pictures."}],
                    GrammarFocus.PAST: [{"sentence": "지난주에 부산에 갔어요.", "translation": "I went to Busan last week."}],
                    GrammarFocus.FUTURE: [{"sentence": "다음 달에 제주도에 갈 거예요.", "translation": "I will go to Jeju next month."}],
                    GrammarFocus.HONORIFIC: [{"sentence": "아버지께서 먼저 호텔을 예약하세요.", "translation": "My father books the hotel first."}],
                    GrammarFocus.CAUSAL: [{"sentence": "날씨가 좋아서 바다에 갔어요.", "translation": "We went to the sea because the weather was nice."}],
                    GrammarFocus.CONTRAST: [{"sentence": "산은 좋지만 바다가 더 좋아요.", "translation": "I like mountains, but I like the sea more."}],
                },
                B2: {
                    GrammarFocus.POLITE_PRESENT: [{"sentence": "여행을 가면 유명한 곳보다 조용한 동네를 더 천천히 둘러봐요.", "translation": "When I travel, I slowly explore quiet neighborhoods rather than famous places."}],
                    GrammarFocus.PAST: [{"sentence": "이번 여행에서는 계획보다 훨씬 많은 곳을 걸어서 둘러봤어요.", "translation": "On this trip, I ended up walking around many more places than planned."}],
                    GrammarFocus.FUTURE: [{"sentence": "다음 여행에서는 현지 시장도 꼭 들러 볼 생각이에요.", "translation": "On my next trip, I plan to stop by a local market too."}],
                    GrammarFocus.HONORIFIC: [{"sentence": "부모님께서 편하게 쉬실 수 있도록 이동 시간을 짧게 잡았어요.", "translation": "I kept travel times short so my parents could rest comfortably."}],
                    GrammarFocus.CAUSAL: [{"sentence": "비행기 시간이 이르지 않아서 아침을 먹고 천천히 출발했어요.", "translation": "Since the flight was not very early, we had breakfast and left slowly."}],
                    GrammarFocus.CONTRAST: [{"sentence": "관광지는 붐볐지만 골목길은 의외로 한적했어요.", "translation": "The tourist area was crowded, but the alleyways were unexpectedly calm."}],
                },
            },
            "restaurant": {
                B1: {
                    GrammarFocus.POLITE_PRESENT: [{"sentence": "저는 김밥을 자주 먹어요.", "translation": "I often eat gimbap."}],
                    GrammarFocus.PAST: [{"sentence": "오늘 점심에 비빔밥을 먹었어요.", "translation": "I ate bibimbap for lunch today."}],
                    GrammarFocus.FUTURE: [{"sentence": "저녁에는 국수를 먹을 거예요.", "translation": "I will eat noodles for dinner."}],
                    GrammarFocus.HONORIFIC: [{"sentence": "어머니께서 먼저 주문하세요.", "translation": "My mother orders first."}],
                    GrammarFocus.CAUSAL: [{"sentence": "배가 고파서 빨리 주문했어요.", "translation": "I ordered quickly because I was hungry."}],
                    GrammarFocus.CONTRAST: [{"sentence": "매운 음식은 좋아하지만 너무 맵지는 않아요.", "translation": "I like spicy food, but not extremely spicy food."}],
                }
            }
        }
