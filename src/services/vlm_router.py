from pathlib import Path

from src.core.exceptions import ProcessingError, ProviderUnavailableError
from src.providers.base import ProviderResult, VLMProvider


class VLMRouterService:
    def __init__(self, providers: list[VLMProvider], enabled: bool) -> None:
        self._providers = providers
        self._enabled = enabled

    def extract(self, document: Path) -> ProviderResult:
        if not self._enabled:
            raise ProviderUnavailableError("VLM fallback is disabled")
        errors: list[str] = []
        for provider in self._providers:
            if not provider.is_available():
                errors.append(f"{provider.name}: unavailable")
                continue
            try:
                return provider.extract(document)
            except (ProcessingError, ProviderUnavailableError) as exc:
                errors.append(f"{provider.name}: {exc}")
        raise ProcessingError("No VLM provider succeeded: " + "; ".join(errors))
