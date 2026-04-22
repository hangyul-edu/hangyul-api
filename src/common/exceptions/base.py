from __future__ import annotations


class AppError(Exception):
    """Base application exception."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ValidationError(AppError):
    status_code = 422
    error_code = "validation_error"


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "forbidden"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class RateLimitedError(AppError):
    status_code = 429
    error_code = "rate_limited"


class SubscriptionRequiredError(AppError):
    """Raised when a non-premium user hits a premium-only path or exhausts the free quota."""

    status_code = 402
    error_code = "subscription_required"
