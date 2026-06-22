from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FieldStatus(StrEnum):
    FOUND = "found"
    MISSING = "missing"


class ExtractedField(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_name: str
    raw_value: str | None
    confidence: float = Field(ge=0, le=1)
    source: Literal["ocr"] = "ocr"
    status: FieldStatus


class ExtractionResult(BaseModel):
    fields: tuple[ExtractedField, ...] = ()
    errors: tuple[str, ...] = ()


class ResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    MISSING = "missing"


class ResolvedField(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_name: str
    raw_value: str | None
    resolved_id: str | int | None = None
    resolved_name: str | None = None
    confidence: float = Field(ge=0, le=1)
    resolver: str
    status: ResolutionStatus
