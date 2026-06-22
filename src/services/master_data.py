from typing import Protocol

from src.core.exceptions import ConfigurationError
from src.models.idp import ExtractedField, ResolvedField, ResolutionStatus
from src.models.templates import DocumentTemplate, ResolverReference
from src.repositories.master_data import MasterDataRepository


class MasterDataResolver(Protocol):
    @property
    def name(self) -> str: ...

    def resolve(self, field: ExtractedField, reference: ResolverReference) -> ResolvedField: ...


class StaticJsonResolver:
    name = "static_json"

    def __init__(self, repository: MasterDataRepository) -> None:
        self._repository = repository

    def resolve(self, field: ExtractedField, reference: ResolverReference) -> ResolvedField:
        if field.raw_value is None:
            return self._result(field, ResolutionStatus.MISSING)
        dataset = self._repository.get(reference.dataset)
        if dataset is None:
            raise ConfigurationError(f"Master data dataset '{reference.dataset}' was not found")
        for entry in dataset.entries:
            if field.raw_value == entry.name:
                return self._result(
                    field,
                    ResolutionStatus.RESOLVED,
                    entry.id,
                    entry.name,
                    1.0,
                )
            if field.raw_value in entry.aliases:
                return self._result(
                    field,
                    ResolutionStatus.RESOLVED,
                    entry.id,
                    entry.name,
                    0.97,
                )
        return self._result(field, ResolutionStatus.NOT_FOUND)

    def _result(
        self,
        field: ExtractedField,
        status: ResolutionStatus,
        resolved_id: str | int | None = None,
        resolved_name: str | None = None,
        confidence: float = 0,
    ) -> ResolvedField:
        return ResolvedField(
            field_name=field.field_name,
            raw_value=field.raw_value,
            resolved_id=resolved_id,
            resolved_name=resolved_name,
            confidence=confidence,
            resolver=self.name,
            status=status,
        )


class MasterDataResolutionService:
    def __init__(self, resolvers: list[MasterDataResolver]) -> None:
        self._resolvers = {resolver.name: resolver for resolver in resolvers}

    def resolve(
        self, fields: tuple[ExtractedField, ...], template: DocumentTemplate
    ) -> tuple[ResolvedField, ...]:
        values = {field.field_name: field for field in fields}
        results: list[ResolvedField] = []
        for definition in template.fields:
            if definition.resolver is None:
                continue
            resolver = self._resolvers.get(definition.resolver.resolver)
            if resolver is None:
                raise ConfigurationError(
                    f"Resolver '{definition.resolver.resolver}' is not configured"
                )
            results.append(resolver.resolve(values[definition.field_name], definition.resolver))
        return tuple(results)
