from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from src.common.api.membership import MembershipSummary

SocialProvider = Literal["google", "apple", "kakao", "facebook", "line"]
PhoneVerificationPurpose = Literal["signup", "recover_email", "reset_password", "change_phone"]


class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    nickname: str = Field(min_length=2, max_length=20)
    marketing_opt_in: bool = False
    terms_accepted: bool = True
    privacy_accepted: bool = True


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SocialLoginRequest(BaseModel):
    provider: SocialProvider
    id_token: str = Field(description="OIDC id_token or provider-issued credential.")
    nonce: str | None = None


class PhoneVerificationStartRequest(BaseModel):
    phone: str = Field(pattern=r"^\+?[1-9]\d{6,14}$", description="E.164 phone number")
    purpose: PhoneVerificationPurpose


class PhoneVerificationStartResponse(BaseModel):
    verification_id: str
    expires_at: datetime
    resend_available_at: datetime


class PhoneVerificationConfirmRequest(BaseModel):
    verification_id: str
    code: str = Field(min_length=4, max_length=8)


class PhoneVerificationConfirmResponse(BaseModel):
    verification_token: str = Field(description="Short-lived token passed to downstream flows.")


class EmailRecoveryRequest(BaseModel):
    verification_token: str


class EmailRecoveryResponse(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    verification_token: str
    new_password: str = Field(min_length=8, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Access-token lifetime in seconds.")
    user_id: str
    is_new_user: bool = False
    membership: "MembershipSummary" = Field(
        description="Current subscription tier at login — so the client can render gated UI immediately.",
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class AccountDeletionRequest(BaseModel):
    password: str | None = None
    reason: str | None = Field(default=None, max_length=500)
