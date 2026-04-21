from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

FaqCategory = Literal["account", "billing", "learning", "technical", "other"]
InquiryCategory = Literal["account", "billing", "bug", "content", "feature_request", "other"]
InquiryStatus = Literal["open", "in_progress", "answered", "closed"]


class Faq(BaseModel):
    faq_id: str
    category: FaqCategory
    question: str
    answer: str
    order: int = 0


class FaqsResponse(BaseModel):
    items: list[Faq]


class InquiryRequest(BaseModel):
    category: InquiryCategory
    subject: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=10, max_length=4000)
    contact_email: EmailStr | None = None
    attachments: list[str] = Field(default_factory=list, description="Pre-signed S3 upload keys.")


class Inquiry(BaseModel):
    inquiry_id: str
    category: InquiryCategory
    subject: str
    body: str
    status: InquiryStatus
    response: str | None = None
    created_at: datetime
    updated_at: datetime


class InquiriesResponse(BaseModel):
    items: list[Inquiry]
