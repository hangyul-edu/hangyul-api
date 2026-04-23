from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.config.settings import get_settings
from src.common.exceptions.handlers import register_exception_handlers
from src.common.logging.logger import configure_logging
from src.modules.ai_chat.presentation.router import router as ai_chat_router
from src.modules.announcements.presentation.router import router as announcements_router
from src.modules.auth.presentation.router import router as auth_router
from src.modules.dashboard.presentation.router import router as dashboard_router
from src.modules.gamification.presentation.router import leagues_router, points_router
from src.modules.learning.presentation.router import (
    courses_router,
    lectures_router,
    learning_router,
    me_learning_router,
    tracks_router,
)
from src.modules.legal.presentation.router import router as legal_router
from src.modules.notifications.presentation.router import router as notifications_router
from src.modules.onboarding.presentation.router import router as onboarding_router
from src.modules.quizzes.presentation.router import router as quizzes_router
from src.modules.recommendations.presentation.router import router as recommendations_router
from src.modules.sentences.presentation.router import (
    router as sentences_router,
    saved_sentences_router,
)
from src.modules.settings.presentation.router import router as settings_router
from src.modules.social.presentation.router import feed_router, friends_router
from src.modules.subscriptions.presentation.router import router as subscriptions_router
from src.modules.support.presentation.router import router as support_router
from src.modules.users.presentation.router import router as users_router
from src.modules.writing.presentation.router import router as writing_router

configure_logging()
settings = get_settings()

tags_metadata = [
    {"name": "auth", "description": "Signup, login (email/social), SMS verification, token rotation, withdrawal."},
    {"name": "users", "description": "Authenticated user profile, nickname, avatar, search by friend code."},
    {"name": "onboarding", "description": "Purpose, speaking level, and TOPIK target capture."},
    {"name": "subscriptions", "description": "Plan catalog, purchase, cancel, restore, purchase history."},
    {"name": "dashboard", "description": "Home dashboard snapshot: streak, goals, next track."},
    {"name": "learning", "description": "Tracks, levels, calendar, stats, lectures and playback."},
    {"name": "sentences", "description": "Sentence study lists, saved sentences (auto + favorite), audio, listen events."},
    {"name": "quizzes", "description": "Daily quiz sets, multiple-choice / fill-blank / typing attempts."},
    {"name": "writing", "description": "Writing prompts and AI-graded submissions."},
    {"name": "ai-chat", "description": "한글AI conversational practice."},
    {"name": "gamification", "description": "Points, league tiers, seasonal rankings."},
    {"name": "social", "description": "Friends by friend-code and activity feed."},
    {"name": "notifications", "description": "In-app notifications and push preferences."},
    {"name": "announcements", "description": "Service announcements."},
    {"name": "support", "description": "FAQs and 1:1 inquiries."},
    {"name": "legal", "description": "Terms, privacy, marketing consent documents."},
    {"name": "settings", "description": "App-level preferences (language, theme, audio, goals)."},
    {"name": "recommendations", "description": "AI sentence recommendation engine (internal)."},
]

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    summary="Korean sentence learning platform API",
    description=(
        "REST API derived from the Figma product design. Authentication is OAuth2 password-flow "
        "with short-lived JWT access tokens + long-lived refresh tokens; social providers "
        "(Google/Apple/Kakao/Facebook/Line) exchange id_tokens for the same envelope. "
        "Errors follow RFC-7807 (application/problem+json)."
    ),
    openapi_tags=tags_metadata,
    swagger_ui_parameters={"persistAuthorization": True, "docExpansion": "none"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/health", tags=["meta"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(onboarding_router)
app.include_router(subscriptions_router)
app.include_router(dashboard_router)
app.include_router(tracks_router)
app.include_router(courses_router)
app.include_router(learning_router)
app.include_router(lectures_router)
app.include_router(me_learning_router)
app.include_router(sentences_router)
app.include_router(saved_sentences_router)
app.include_router(quizzes_router)
app.include_router(writing_router)
app.include_router(ai_chat_router)
app.include_router(points_router)
app.include_router(leagues_router)
app.include_router(friends_router)
app.include_router(feed_router)
app.include_router(notifications_router)
app.include_router(announcements_router)
app.include_router(support_router)
app.include_router(legal_router)
app.include_router(settings_router)
app.include_router(recommendations_router)
