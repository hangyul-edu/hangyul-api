from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.common.exceptions import UnauthorizedError
from src.common.security.tokens import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/email", auto_error=False)


@dataclass
class CurrentUser:
    user_id: str
    token_id: str


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> CurrentUser:
    if not token:
        raise UnauthorizedError("Missing bearer token.")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Access token has expired.") from None
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid access token.") from None
    if payload.get("typ") != "access":
        raise UnauthorizedError("Wrong token type; access token required.")
    return CurrentUser(user_id=payload["sub"], token_id=payload["jti"])
