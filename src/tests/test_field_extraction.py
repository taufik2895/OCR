from src.models.idp import FieldStatus
from src.models.templates import DocumentTemplate
from src.services.field_extraction import FieldExtractionService


def make_template() -> DocumentTemplate:
    return DocumentTemplate.model_validate(
        {
            "template_id": "land-record",
            "version": 1,
            "display_name": "Land Record",
            "fields": [
                {
                    "field_name": "region",
                    "required": True,
                    "rule": {"strategy": "label", "label": "Region"},
                },
                {
                    "field_name": "owner",
                    "rule": {
                        "strategy": "regex",
                        "pattern": "Owner=(?P<value>[^\\r\\n]+)",
                    },
                },
                {
                    "field_name": "missing",
                    "required": True,
                    "rule": {"strategy": "label", "label": "Missing"},
                },
            ],
        }
    )


def test_extracts_raw_values_without_normalization() -> None:
    text = "Region: KABUPATEN BOGOR  \nOwner=  TAUFIK  "
    result = FieldExtractionService().extract(text, 0.95, make_template())
    fields = {field.field_name: field for field in result.fields}
    assert fields["region"].raw_value == "KABUPATEN BOGOR  "
    assert fields["owner"].raw_value == "  TAUFIK  "
    assert fields["missing"].raw_value is None
    assert fields["missing"].status == FieldStatus.MISSING
    assert fields["missing"].confidence == 0
    assert result.errors == ("Required field 'missing' was not found",)


def test_regex_without_capture_returns_exact_match() -> None:
    template = DocumentTemplate.model_validate(
        {
            "template_id": "simple",
            "version": 1,
            "display_name": "Simple",
            "fields": [{"field_name": "code", "rule": {"strategy": "regex", "pattern": "ABC-123"}}],
        }
    )
    result = FieldExtractionService().extract("Code ABC-123 end", 0.8, template)
    assert result.fields[0].raw_value == "ABC-123"
