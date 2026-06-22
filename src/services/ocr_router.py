import logging
from pathlib import Path

from src.core.exceptions import ProcessingError, ProviderUnavailableError
from src.providers.base import OCRProvider, ProviderResult

logger = logging.getLogger(__name__)


class OCRRouterService:
    def __init__(self, providers: list[OCRProvider]) -> None:
        self._providers = providers

    def extract(self, document: Path) -> ProviderResult:
        errors: list[str] = []
        for provider in self._providers:
            if not provider.is_available():
                errors.append(f"{provider.name}: unavailable")
                continue
            try:
                result = provider.extract(document)
                if result.text.strip():
                    return result
                errors.append(f"{provider.name}: empty result")
            except (ProcessingError, ProviderUnavailableError) as exc:
                logger.warning(
                    "ocr_provider_failed", extra={"provider": provider.name, "error": str(exc)}
                )
                errors.append(f"{provider.name}: {exc}")
        raise ProcessingError("No OCR provider succeeded: " + "; ".join(errors))
