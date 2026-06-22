import re

from src.models.idp import ExtractedField, ExtractionResult, FieldStatus
from src.models.templates import DocumentTemplate, FieldExtractionRule


class FieldExtractionService:
    _flag_map = {"IGNORECASE": re.IGNORECASE, "MULTILINE": re.MULTILINE}

    def extract(
        self, text: str, ocr_confidence: float, template: DocumentTemplate
    ) -> ExtractionResult:
        fields: list[ExtractedField] = []
        errors: list[str] = []
        for definition in template.fields:
            raw_value = self._capture(text, definition.rule)
            status = FieldStatus.FOUND if raw_value is not None else FieldStatus.MISSING
            confidence = ocr_confidence if raw_value is not None else 0.0
            fields.append(
                ExtractedField(
                    field_name=definition.field_name,
                    raw_value=raw_value,
                    confidence=round(confidence, 4),
                    status=status,
                )
            )
            if definition.required and raw_value is None:
                errors.append(f"Required field '{definition.field_name}' was not found")
        return ExtractionResult(fields=tuple(fields), errors=tuple(errors))

    def _capture(self, text: str, rule: FieldExtractionRule) -> str | None:
        flags = self._flags(rule)
        if rule.strategy == "label":
            pattern = rf"{re.escape(rule.label or '')}{rule.separator_pattern}(?P<value>[^\r\n]*)"
            match = re.search(pattern, text, flags)
        else:
            match = re.search(rule.pattern or "", text, flags)
        if match is None:
            return None
        if "value" in match.re.groupindex:
            return match.group("value")
        if match.lastindex:
            return match.group(1)
        return match.group(0)

    def _flags(self, rule: FieldExtractionRule) -> re.RegexFlag:
        flags = re.RegexFlag(0)
        for name in rule.flags:
            flags |= self._flag_map[name]
        return flags
