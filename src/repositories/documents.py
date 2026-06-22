import json
import threading
from pathlib import Path
from typing import Protocol
from uuid import UUID

from src.models.document import Document


class DocumentRepository(Protocol):
    def save(self, document: Document) -> Document: ...
    def get(self, document_id: UUID) -> Document | None: ...
    def list(self, limit: int = 100) -> list[Document]: ...


class JsonDocumentRepository:
    """Small durable repository; replace with SQL without changing services."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._lock = threading.RLock()
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, document: Document) -> Document:
        target = self._directory / f"{document.id}.json"
        temporary = target.with_suffix(".tmp")
        with self._lock:
            temporary.write_text(document.model_dump_json(indent=2), encoding="utf-8")
            temporary.replace(target)
        return document

    def get(self, document_id: UUID) -> Document | None:
        target = self._directory / f"{document_id}.json"
        if not target.exists():
            return None
        with self._lock:
            return Document.model_validate_json(target.read_text(encoding="utf-8"))

    def list(self, limit: int = 100) -> list[Document]:
        documents: list[Document] = []
        with self._lock:
            paths = sorted(
                self._directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True
            )
            for path in paths[:limit]:
                try:
                    documents.append(Document.model_validate_json(path.read_text(encoding="utf-8")))
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
        return documents
