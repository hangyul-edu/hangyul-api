from __future__ import annotations

from fastapi import APIRouter, Depends

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.settings.presentation.schemas import (
    AppSettings,
    UpdateAppSettingsRequest,
    UpdateContactAccessRequest,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/me", response_model=AppSettings, summary="Get my app settings")
def get_my_settings(user: CurrentUser = Depends(get_current_user)) -> AppSettings:
    return AppSettings()


@router.put("/me", response_model=AppSettings, summary="Update my app settings")
def update_my_settings(
    payload: UpdateAppSettingsRequest, user: CurrentUser = Depends(get_current_user)
) -> AppSettings:
    merged = AppSettings().model_dump()
    for k, v in payload.model_dump(exclude_none=True).items():
        merged[k] = v
    return AppSettings(**merged)


@router.put(
    "/me/contact-access",
    response_model=AppSettings,
    summary="Record the user's choice from the 'allow contacts' modal",
    description=(
        "Dedicated endpoint for the separate contacts-consent modal. Writes "
        "`contact_access_granted` into the user's settings and returns the updated AppSettings. "
        "Required to be `true` for address-book friend invites (§4.12) and phone-book ranking "
        "comparisons (§4.11)."
    ),
)
def update_contact_access(
    payload: UpdateContactAccessRequest,
    user: CurrentUser = Depends(get_current_user),
) -> AppSettings:
    merged = AppSettings().model_dump()
    merged["contact_access_granted"] = payload.granted
    return AppSettings(**merged)
