import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class FieldExtractionRule(BaseModel):
    strategy: Literal["label", "regex"]
    label: str | None = None
    pattern: str | None = None
    separator_pattern: str = r"[ \t]*[:=][ \t]*"
    flags: list[Literal["IGNORECASE", "MULTILINE"]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_strategy_configuration(self) -> "FieldExtractionRule":
        if self.strategy == "label" and not self.label:
            raise ValueError("label strategy requires label")
        if self.strategy == "regex" and not self.pattern:
            raise ValueError("regex strategy requires pattern")
        for expression in filter(None, (self.pattern, self.separator_pattern)):
            try:
                re.compile(expression)
            except re.error as exc:
                raise ValueError(f"invalid regular expression: {exc}") from exc
        return self


class ResolverReference(BaseModel):
    resolver: Literal["static_json"]
    dataset: str = Field(min_length=1, pattern=r"^[A-Za-z0-9._-]+$")


class TemplateField(BaseModel):
    field_name: str = Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    required: bool = False
    rule: FieldExtractionRule
    resolver: ResolverReference | None = None


class PayloadMapping(BaseModel):
    target_path: str = Field(
        min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)*$"
    )
    source_field: str = Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    value_selector: Literal["raw_value", "resolved_id", "resolved_name"] = "raw_value"
    required: bool = False


class DocumentTemplate(BaseModel):
    schema_version: Literal[1] = 1
    template_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    version: Annotated[int, Field(gt=0)]
    display_name: str = Field(min_length=1)
    fields: list[TemplateField] = Field(min_length=1)
    payload_mappings: list[PayloadMapping] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_references(self) -> "DocumentTemplate":
        field_names = [field.field_name for field in self.fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError("field names must be unique")
        target_paths = [mapping.target_path for mapping in self.payload_mappings]
        if len(target_paths) != len(set(target_paths)):
            raise ValueError("payload target paths must be unique")
        unknown = {
            mapping.source_field
            for mapping in self.payload_mappings
            if mapping.source_field not in field_names
        }
        if unknown:
            raise ValueError(f"payload mappings reference unknown fields: {sorted(unknown)}")
        return self


class TemplateSummary(BaseModel):
    template_id: str
    version: int
    display_name: str
    field_count: int
