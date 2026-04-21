from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

import jwt

from src.common.config.settings import get_settings

TokenKind = Literal["access", "refresh"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(subject: str, kind: TokenKind) -> tuple[str, datetime]:
    settings = get_settings()
    now = _now()
    if kind == "access":
        exp = now + timedelta(minutes=settings.access_token_ttl_minutes)
    else:
        exp = now + timedelta(days=settings.refresh_token_ttl_days)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid4()),
        "typ": kind,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, exp


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
