from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from src.core.exceptions import ConfigurationError
from src.models.templates import DocumentTemplate, TemplateSummary


class TemplateRepository(Protocol):
    def get(self, template_id: str, version: int | None = None) -> DocumentTemplate | None: ...
    def list(self) -> list[TemplateSummary]: ...


class JsonTemplateRepository:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def get(self, template_id: str, version: int | None = None) -> DocumentTemplate | None:
        matches = [
            template
            for template in self._load_all()
            if template.template_id == template_id
            and (version is None or template.version == version)
        ]
        return max(matches, key=lambda item: item.version) if matches else None

    def list(self) -> list[TemplateSummary]:
        latest: dict[str, DocumentTemplate] = {}
        for template in self._load_all():
            current = latest.get(template.template_id)
            if current is None or template.version > current.version:
                latest[template.template_id] = template
        return [
            TemplateSummary(
                template_id=item.template_id,
                version=item.version,
                display_name=item.display_name,
                field_count=len(item.fields),
            )
            for item in sorted(latest.values(), key=lambda value: value.template_id)
        ]

    def _load_all(self) -> list[DocumentTemplate]:
        templates: list[DocumentTemplate] = []
        identities: set[tuple[str, int]] = set()
        for path in sorted(self._directory.glob("*.json")):
            try:
                template = DocumentTemplate.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, ValidationError) as exc:
                raise ConfigurationError(f"Invalid template {path.name}: {exc}") from exc
            identity = (template.template_id, template.version)
            if identity in identities:
                raise ConfigurationError(
                    f"Duplicate template identity {template.template_id} v{template.version}"
                )
            identities.add(identity)
            templates.append(template)
        return templates
