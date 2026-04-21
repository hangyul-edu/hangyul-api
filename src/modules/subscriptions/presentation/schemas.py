from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PlanInterval = Literal["month", "year"]
BillingProvider = Literal["stripe", "apple", "google"]
SubscriptionStatus = Literal["active", "trialing", "past_due", "canceled", "expired"]


class SubscriptionPlan(BaseModel):
    plan_id: str
    name: str
    description: str | None = None
    price_cents: int
    currency: str = "USD"
    interval: PlanInterval
    trial_days: int = 0
    promo_price_cents: int | None = None
    features: list[str] = Field(default_factory=list)


class PlansResponse(BaseModel):
    plans: list[SubscriptionPlan]


class MySubscription(BaseModel):
    subscription_id: str | None
    plan_id: str | None
    status: SubscriptionStatus
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    provider: BillingProvider | None = None


class CheckoutRequest(BaseModel):
    plan_id: str
    provider: BillingProvider = "stripe"
    promo_code: str | None = None
    success_url: str | None = None
    cancel_url: str | None = None


class CheckoutResponse(BaseModel):
    checkout_session_id: str
    redirect_url: str | None = None
    provider: BillingProvider
    client_secret: str | None = Field(default=None, description="For native payment sheets.")


class CancelResponse(BaseModel):
    subscription_id: str
    cancel_at_period_end: bool
    current_period_end: datetime


class Purchase(BaseModel):
    purchase_id: str
    plan_id: str
    plan_name: str
    amount_cents: int
    currency: str
    purchased_at: datetime
    provider: BillingProvider
    receipt_url: str | None = None


class PurchasesResponse(BaseModel):
    items: list[Purchase]
