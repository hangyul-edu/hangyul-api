from __future__ import annotations

from fastapi import APIRouter, Depends

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.settings.presentation.schemas import AppSettings, UpdateAppSettingsRequest

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/me", response_model=AppSettings, summary="Get my app settings")
def get_my_settings(user: CurrentUser = Depends(get_current_user)) -> AppSettings:
    return AppSettings()


@router.put("/me", response_model=AppSettings, summary="Update my app settings")
def update_my_settings(
    payload: UpdateAppSettingsRequest, user: CurrentUser = Depends(get_current_user)
) -> AppSettings:
    return AppSettings()
