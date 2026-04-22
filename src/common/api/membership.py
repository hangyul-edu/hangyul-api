from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MembershipTier = Literal["free", "trial", "premium"]


class MembershipSummary(BaseModel):
    """Compact subscription state embedded in every login response and /users/me."""

    tier: MembershipTier = Field(
        description=(
            "'premium' — paid subscriber; 'trial' — within the 7-day free trial; "
            "'free' — non-subscribed member."
        )
    )
    is_premium: bool = Field(
        description=(
            "Convenience flag: true iff tier ∈ {'trial', 'premium'}. "
            "Clients should treat free trial the same as paid for feature gating."
        )
    )
    expires_at: datetime | None = Field(
        default=None,
        description=(
            "When the trial / paid access ends. Null for 'free'. "
            "Equals MySubscription.expires_at (see §4.4)."
        ),
    )
