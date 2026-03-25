from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.config.settings import get_settings
from src.common.logging.logger import configure_logging
from src.modules.recommendations.presentation.router import router as recommendations_router
from src.modules.users.presentation.router import router as users_router

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(recommendations_router)
