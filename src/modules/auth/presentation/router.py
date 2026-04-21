from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.common.config.settings import get_settings
from src.common.security.auth import CurrentUser, get_current_user
from src.common.security.tokens import create_token
from src.modules.auth.presentation.schemas import (
    AccountDeletionRequest,
    EmailLoginRequest,
    EmailRecoveryRequest,
    EmailRecoveryResponse,
    EmailSignupRequest,
    LogoutRequest,
    PasswordResetRequest,
    PhoneVerificationConfirmRequest,
    PhoneVerificationConfirmResponse,
    PhoneVerificationStartRequest,
    PhoneVerificationStartResponse,
    RefreshTokenRequest,
    SocialLoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user_id: str, is_new_user: bool = False) -> TokenResponse:
    access, access_exp = create_token(user_id, "access")
    refresh, _ = create_token(user_id, "refresh")
    settings = get_settings()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_ttl_minutes * 60,
        user_id=user_id,
        is_new_user=is_new_user,
    )


@router.post(
    "/signup/email",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register with email & password",
)
def signup_email(payload: EmailSignupRequest) -> TokenResponse:
    user_id = f"usr_{uuid4().hex[:12]}"
    return _issue_tokens(user_id, is_new_user=True)


@router.post("/login/email", response_model=TokenResponse, summary="Login with email & password")
def login_email(payload: EmailLoginRequest) -> TokenResponse:
    return _issue_tokens(f"usr_{uuid4().hex[:12]}")


@router.post(
    "/login/oauth2",
    response_model=TokenResponse,
    summary="OAuth2 password-flow endpoint consumed by Swagger UI",
    include_in_schema=True,
)
def login_oauth2(form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    return _issue_tokens(f"usr_{uuid4().hex[:12]}")


@router.post("/login/social", response_model=TokenResponse, summary="Social login (Google/Apple/Kakao/Facebook/Line)")
def login_social(payload: SocialLoginRequest) -> TokenResponse:
    return _issue_tokens(f"usr_{uuid4().hex[:12]}", is_new_user=False)


@router.post(
    "/phone/verification",
    response_model=PhoneVerificationStartResponse,
    summary="Start SMS verification",
)
def start_phone_verification(payload: PhoneVerificationStartRequest) -> PhoneVerificationStartResponse:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return PhoneVerificationStartResponse(
        verification_id=f"ver_{uuid4().hex[:12]}",
        expires_at=now + timedelta(minutes=5),
        resend_available_at=now + timedelta(seconds=60),
    )


@router.post(
    "/phone/verification/confirm",
    response_model=PhoneVerificationConfirmResponse,
    summary="Confirm SMS verification code",
)
def confirm_phone_verification(payload: PhoneVerificationConfirmRequest) -> PhoneVerificationConfirmResponse:
    return PhoneVerificationConfirmResponse(verification_token=f"vt_{uuid4().hex[:24]}")


@router.post(
    "/email/recover",
    response_model=EmailRecoveryResponse,
    summary="Recover registered email using phone verification",
)
def recover_email(payload: EmailRecoveryRequest) -> EmailRecoveryResponse:
    return EmailRecoveryResponse(email="h***@example.com")


@router.post(
    "/password/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password after phone verification",
)
def reset_password(payload: PasswordResetRequest) -> None:
    return None


@router.post("/token/refresh", response_model=TokenResponse, summary="Rotate access & refresh tokens")
def refresh_token(payload: RefreshTokenRequest) -> TokenResponse:
    return _issue_tokens(f"usr_{uuid4().hex[:12]}")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke refresh token")
def logout(payload: LogoutRequest, user: CurrentUser = Depends(get_current_user)) -> None:
    return None


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Withdraw account",
)
def delete_account(payload: AccountDeletionRequest, user: CurrentUser = Depends(get_current_user)) -> None:
    return None
