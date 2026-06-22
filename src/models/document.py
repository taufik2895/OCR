from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.idp import ExtractedField, ResolvedField


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRResult(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)
    provider: str
    used_vlm: bool = False
    template_id: str | None = None
    template_version: int | None = None
    extracted_fields: tuple[ExtractedField, ...] = ()
    extraction_errors: tuple[str, ...] = ()
    resolutions: tuple[ResolvedField, ...] = ()
    warnings: list[str] = Field(default_factory=list)


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    original_name: str
    content_type: str
    size_bytes: int = Field(ge=0)
    checksum_sha256: str
    storage_path: Path
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    result: OCRResult | None = None
    error: str | None = None
