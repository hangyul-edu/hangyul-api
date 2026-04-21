from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

LegalDocumentKind = Literal["terms", "privacy", "marketing_consent", "age_verification"]


class LegalDocument(BaseModel):
    kind: LegalDocumentKind
    version: str
    locale: str = "ko"
    effective_date: date
    body_markdown: str
    body_html: str | None = None
