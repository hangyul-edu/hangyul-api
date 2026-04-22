from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PlanInterval = Literal["month", "year"]
BillingMode = Literal["recurring", "one_time"]
BillingProvider = Literal["stripe", "apple", "google"]
SubscriptionStatus = Literal["trial", "active", "past_due", "canceled", "expired"]


class SubscriptionPlan(BaseModel):
    plan_id: str
    name: str
    description: str | None = None
    price_cents: int
    currency: str = "USD"
    interval: PlanInterval = Field(
        description=(
            "Billing cadence. 'month' = auto-renewing monthly; 'year' = single 12-month charge."
        )
    )
    billing_mode: BillingMode = Field(
        description=(
            "Whether the plan auto-renews. Monthly plans are 'recurring'; the 12-month plan is "
            "'one_time' — a single charge covering 12 months of access, no automatic renewal."
        )
    )
    trial_days: int = Field(
        default=0,
        ge=0,
        description="Number of free-trial days granted on first signup for this plan (e.g. 7).",
    )
    promo_price_cents: int | None = None
    features: list[str] = Field(default_factory=list)


class PlansResponse(BaseModel):
    plans: list[SubscriptionPlan]


class MySubscription(BaseModel):
    subscription_id: str | None = None
    plan_id: str | None = None
    status: SubscriptionStatus
    provider: BillingProvider | None = None
    interval: PlanInterval | None = Field(
        default=None, description="Cadence of the active plan. Null until a plan is chosen."
    )
    billing_mode: BillingMode | None = Field(
        default=None, description="Whether the active plan auto-renews or was a one-time 12-month charge."
    )

    # Trial lifecycle ------------------------------------------------------------
    trial_started: bool = Field(
        default=False,
        description="True iff the user has ever begun a free trial (latches on first trial start).",
    )
    trial_started_at: datetime | None = Field(
        default=None, description="Timestamp the free trial began; null when the user never started one."
    )
    trial_expires_at: datetime | None = Field(
        default=None,
        description="Timestamp the free trial ends — typically trial_started_at + plan.trial_days.",
    )
    in_trial: bool = Field(
        default=False,
        description="Convenience flag: true iff now is between trial_started_at and trial_expires_at.",
    )

    # Billing period -------------------------------------------------------------
    current_period_start: datetime | None = Field(
        default=None,
        description="Start of the current paid billing cycle (monthly plan). Null before first charge.",
    )
    current_period_end: datetime | None = Field(
        default=None,
        description="End of the current paid billing cycle (monthly plan).",
    )

    # Canonical access expiration ------------------------------------------------
    expires_at: datetime | None = Field(
        default=None,
        description=(
            "When access ends if nothing else changes. For a user still in trial this equals "
            "trial_expires_at. For a monthly recurring plan this equals the next current_period_end. "
            "For the one-time 12-month plan this equals the single-purchase expiration date."
        ),
    )

    cancel_at_period_end: bool = False


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
    current_period_end: datetime | None = None
    expires_at: datetime | None = Field(
        default=None, description="Effective access end after the cancel request."
    )


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
