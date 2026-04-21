from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.subscriptions.presentation.schemas import (
    CancelResponse,
    CheckoutRequest,
    CheckoutResponse,
    MySubscription,
    PlansResponse,
    Purchase,
    PurchasesResponse,
    SubscriptionPlan,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=PlansResponse, summary="List available subscription plans")
def list_plans() -> PlansResponse:
    return PlansResponse(
        plans=[
            SubscriptionPlan(
                plan_id="plan_monthly",
                name="Monthly",
                price_cents=799,
                promo_price_cents=599,
                interval="month",
                trial_days=7,
                features=["모든 레슨", "AI 한글 튜터", "광고 제거"],
            ),
            SubscriptionPlan(
                plan_id="plan_yearly",
                name="Yearly",
                price_cents=5400,
                interval="year",
                features=["모든 레슨", "AI 한글 튜터", "광고 제거", "프리미엄 콘텐츠"],
            ),
        ]
    )


@router.get("/me", response_model=MySubscription, summary="Get my subscription state")
def get_my_subscription(user: CurrentUser = Depends(get_current_user)) -> MySubscription:
    return MySubscription(subscription_id=None, plan_id=None, status="expired")


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a checkout session",
)
def create_checkout(payload: CheckoutRequest, user: CurrentUser = Depends(get_current_user)) -> CheckoutResponse:
    return CheckoutResponse(
        checkout_session_id="cs_test_123",
        redirect_url="https://checkout.example.com/cs_test_123",
        provider=payload.provider,
        client_secret=None,
    )


@router.post("/cancel", response_model=CancelResponse, summary="Cancel active subscription")
def cancel_subscription(user: CurrentUser = Depends(get_current_user)) -> CancelResponse:
    return CancelResponse(
        subscription_id="sub_123",
        cancel_at_period_end=True,
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )


@router.post("/restore", response_model=MySubscription, summary="Restore purchases")
def restore_purchases(user: CurrentUser = Depends(get_current_user)) -> MySubscription:
    return MySubscription(subscription_id=None, plan_id=None, status="expired")


@router.get("/purchases", response_model=PurchasesResponse, summary="Get purchase history")
def list_purchases(user: CurrentUser = Depends(get_current_user)) -> PurchasesResponse:
    return PurchasesResponse(items=[])
