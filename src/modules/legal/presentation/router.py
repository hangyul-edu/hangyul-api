from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from src.modules.legal.presentation.schemas import LegalDocument, LegalDocumentKind

router = APIRouter(prefix="/legal", tags=["legal"])


def _stub(kind: LegalDocumentKind) -> LegalDocument:
    return LegalDocument(
        kind=kind,
        version="1.0",
        locale="ko",
        effective_date=date(2026, 1, 1),
        body_markdown="# 한글 서비스 약관/정책\n...",
    )


@router.get("/terms", response_model=LegalDocument, summary="Terms of service")
def get_terms(locale: str = "ko") -> LegalDocument:
    return _stub("terms")


@router.get("/privacy", response_model=LegalDocument, summary="Privacy policy")
def get_privacy(locale: str = "ko") -> LegalDocument:
    return _stub("privacy")


@router.get("/marketing-consent", response_model=LegalDocument, summary="Marketing consent terms")
def get_marketing(locale: str = "ko") -> LegalDocument:
    return _stub("marketing_consent")
