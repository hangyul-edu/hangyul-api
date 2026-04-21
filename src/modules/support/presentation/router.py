from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.support.presentation.schemas import (
    FaqCategory,
    FaqsResponse,
    InquiriesResponse,
    Inquiry,
    InquiryRequest,
)

router = APIRouter(prefix="/support", tags=["support"])


@router.get("/faqs", response_model=FaqsResponse, summary="List FAQs")
def list_faqs(category: FaqCategory | None = Query(None)) -> FaqsResponse:
    return FaqsResponse(items=[])


@router.get("/faqs/{faq_id}", response_model=dict, summary="Get a single FAQ")
def get_faq(faq_id: str) -> dict:
    return {"faq_id": faq_id}


@router.post(
    "/inquiries",
    response_model=Inquiry,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a 1:1 inquiry",
)
def submit_inquiry(payload: InquiryRequest, user: CurrentUser = Depends(get_current_user)) -> Inquiry:
    now = datetime.now(timezone.utc)
    return Inquiry(
        inquiry_id=f"inq_{uuid4().hex[:12]}",
        category=payload.category,
        subject=payload.subject,
        body=payload.body,
        status="open",
        response=None,
        created_at=now,
        updated_at=now,
    )


@router.get("/inquiries/me", response_model=InquiriesResponse, summary="List my inquiries")
def list_my_inquiries(user: CurrentUser = Depends(get_current_user)) -> InquiriesResponse:
    return InquiriesResponse(items=[])


@router.get("/inquiries/{inquiry_id}", response_model=Inquiry, summary="Get inquiry detail")
def get_inquiry(inquiry_id: str, user: CurrentUser = Depends(get_current_user)) -> Inquiry:
    now = datetime.now(timezone.utc)
    return Inquiry(
        inquiry_id=inquiry_id,
        category="other",
        subject="",
        body="",
        status="open",
        response=None,
        created_at=now,
        updated_at=now,
    )
