import re
from typing import Any


class StructuredExtractionService:
    """Deterministic general-document extraction; field schemas can replace it."""

    def extract(self, text: str, requested_fields: list[str]) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        key_values: dict[str, str] = {}
        for line in lines:
            match = re.match(r"^([^:]{2,80}):\s*(.+)$", line)
            if match:
                key_values[self._normalize(match.group(1))] = match.group(2).strip()
        if requested_fields:
            return {field: self._find_field(field, key_values, lines) for field in requested_fields}
        return {
            "fields": key_values,
            "emails": sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.\w+", text))),
            "dates": sorted(set(re.findall(r"\b\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b", text))),
            "line_count": len(lines),
        }

    def _find_field(self, field: str, key_values: dict[str, str], lines: list[str]) -> str | None:
        normalized = self._normalize(field)
        if normalized in key_values:
            return key_values[normalized]
        pattern = re.compile(rf"\b{re.escape(field)}\b\s*[:=-]?\s*(.+)", re.IGNORECASE)
        return next(
            (match.group(1).strip() for line in lines if (match := pattern.search(line))), None
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
