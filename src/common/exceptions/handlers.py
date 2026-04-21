from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.common.exceptions.base import AppError


def problem(status: int, code: str, title: str, detail: str, instance: str) -> dict:
    return {
        "type": f"about:blank#{code}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail,
        "instance": instance,
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=problem(
                status=exc.status_code,
                code=exc.error_code,
                title=exc.__class__.__name__,
                detail=exc.message,
                instance=str(request.url.path),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=problem(
                status=exc.status_code,
                code=f"http_{exc.status_code}",
                title="HTTPException",
                detail=str(exc.detail),
                instance=str(request.url.path),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                **problem(
                    status=422,
                    code="validation_error",
                    title="ValidationError",
                    detail="One or more fields failed validation.",
                    instance=str(request.url.path),
                ),
                "errors": exc.errors(),
            },
        )
