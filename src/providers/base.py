from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class ProviderResult(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)
    provider: str
    page_count: int = Field(default=1, ge=1)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class OCRProvider(Protocol):
    @property
    def name(self) -> str: ...
    def is_available(self) -> bool: ...
    def extract(self, document: Path) -> ProviderResult: ...


class VLMProvider(Protocol):
    @property
    def name(self) -> str: ...
    def is_available(self) -> bool: ...
    def extract(self, document: Path) -> ProviderResult: ...
