class AppError(Exception):
    """Base application exception."""


class NotFoundError(AppError):
    """Raised when an entity cannot be found."""


class ValidationError(AppError):
    """Raised when application validation fails."""
