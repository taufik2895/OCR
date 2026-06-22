import csv
import io
import json
from typing import Any

from openpyxl import Workbook

from src.models.document import Document


class ExportService:
    _content_types = {
        "txt": "text/plain; charset=utf-8",
        "json": "application/json",
        "csv": "text/csv; charset=utf-8",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    def export(self, document: Document, output_format: str) -> tuple[bytes, str]:
        if document.result is None:
            raise ValueError("Document has no completed result")
        fields = [field.model_dump(mode="json") for field in document.result.extracted_fields]
        exporters = {
            "txt": lambda: document.result.text.encode("utf-8"),
            "json": lambda: json.dumps(
                document.result.model_dump(mode="json"), ensure_ascii=False, indent=2
            ).encode("utf-8"),
            "csv": lambda: self._csv({"extracted_fields": fields}),
            "xlsx": lambda: self._xlsx({"extracted_fields": fields}),
        }
        if output_format not in exporters:
            raise ValueError("Unsupported export format")
        return exporters[output_format](), self._content_types[output_format]

    def _csv(self, data: dict[str, Any]) -> bytes:
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["field", "value"])
        for key, value in self._flatten(data):
            writer.writerow([key, value])
        return stream.getvalue().encode("utf-8-sig")

    def _xlsx(self, data: dict[str, Any]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "OCR Result"
        sheet.append(["Field", "Value"])
        for key, value in self._flatten(data):
            sheet.append([key, str(value)])
        stream = io.BytesIO()
        workbook.save(stream)
        return stream.getvalue()

    def _flatten(self, data: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
        rows: list[tuple[str, Any]] = []
        for key, value in data.items():
            name = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                rows.extend(self._flatten(value, name))
            elif isinstance(value, list):
                rows.append((name, ", ".join(map(str, value))))
            else:
                rows.append((name, value))
        return rows
