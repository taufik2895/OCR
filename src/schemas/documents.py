from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.document import DocumentStatus
from src.models.idp import ExtractedField, ResolvedField


class UploadResponse(BaseModel):
    id: UUID
    filename: str
    status: DocumentStatus
    size_bytes: int


class ProcessRequest(BaseModel):
    template_id: str | None = Field(default=None, min_length=1)
    template_version: int | None = Field(default=None, gt=0)
    force: bool = False


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    filename: str
    status: DocumentStatus
    text: str = ""
    confidence: float | None = None
    provider: str | None = None
    used_vlm: bool = False
    template_id: str | None = None
    template_version: int | None = None
    extracted_fields: list[ExtractedField] = Field(default_factory=list)
    extraction_errors: list[str] = Field(default_factory=list)
    resolutions: list[ResolvedField] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentSummary(BaseModel):
    id: UUID
    filename: str
    status: DocumentStatus
    confidence: float | None
    provider: str | None
    created_at: datetime


class DashboardResponse(BaseModel):
    total: int
    completed: int
    failed: int
    average_confidence: float
