import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from src.core.exceptions import DocumentNotFoundError, ProcessingError, ProviderUnavailableError
from src.models.document import Document, DocumentStatus, OCRResult
from src.models.idp import ExtractionResult
from src.providers.base import ProviderResult
from src.repositories.documents import DocumentRepository
from src.repositories.templates import TemplateRepository
from src.services.confidence import ConfidenceService
from src.services.field_extraction import FieldExtractionService
from src.services.master_data import MasterDataResolutionService
from src.services.native_extraction import NativeTextExtractionService
from src.services.ocr_router import OCRRouterService
from src.services.rasterization import RasterizationService
from src.services.validation import ValidationService
from src.services.vlm_router import VLMRouterService

logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(
        self,
        repository: DocumentRepository,
        native: NativeTextExtractionService,
        rasterizer: RasterizationService,
        ocr_router: OCRRouterService,
        vlm_router: VLMRouterService,
        confidence: ConfidenceService,
        validator: ValidationService,
        templates: TemplateRepository,
        field_extractor: FieldExtractionService,
        master_data: MasterDataResolutionService,
        threshold: float,
    ) -> None:
        self._repository = repository
        self._native = native
        self._rasterizer = rasterizer
        self._ocr_router = ocr_router
        self._vlm_router = vlm_router
        self._confidence = confidence
        self._validator = validator
        self._templates = templates
        self._field_extractor = field_extractor
        self._master_data = master_data
        self._threshold = threshold

    def process(
        self,
        document_id: UUID,
        template_id: str | None,
        template_version: int | None,
        force: bool = False,
    ) -> Document:
        document = self._repository.get(document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found")
        if document.status == DocumentStatus.COMPLETED and not force:
            return document
        document.status = DocumentStatus.PROCESSING
        document.error = None
        self._touch(document)
        self._repository.save(document)
        logger.info("processing_started", extra={"document_id": str(document.id)})
        try:
            result = self._extract(document.storage_path)
            score = self._confidence.evaluate(result)
            used_vlm = False
            warnings: list[str] = []
            if score < self._threshold:
                try:
                    vlm_result = self._extract_pages(document.storage_path, use_vlm=True)
                    vlm_score = self._confidence.evaluate(vlm_result)
                    if vlm_score >= score:
                        result, score, used_vlm = vlm_result, vlm_score, True
                except (ProcessingError, ProviderUnavailableError) as exc:
                    warnings.append(f"VLM fallback unavailable: {exc}")
            warnings.extend(self._validator.validate(result.text))
            template = self._templates.get(template_id, template_version) if template_id else None
            if template_id and template is None:
                raise DocumentNotFoundError("Document template not found")
            extraction = (
                self._field_extractor.extract(result.text, score, template)
                if template
                else ExtractionResult()
            )
            resolutions = (
                self._master_data.resolve(extraction.fields, template) if template else ()
            )
            document.result = OCRResult(
                text=result.text,
                confidence=score,
                provider=result.provider,
                used_vlm=used_vlm,
                template_id=template.template_id if template else None,
                template_version=template.version if template else None,
                extracted_fields=extraction.fields,
                extraction_errors=extraction.errors,
                resolutions=resolutions,
                warnings=warnings,
            )
            document.status = DocumentStatus.COMPLETED
            logger.info(
                "processing_completed",
                extra={
                    "document_id": str(document.id),
                    "provider": result.provider,
                    "confidence": score,
                },
            )
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.error = str(exc)
            logger.exception("processing_failed", extra={"document_id": str(document.id)})
            self._touch(document)
            self._repository.save(document)
            raise
        self._touch(document)
        return self._repository.save(document)

    def _extract(self, path: Path) -> ProviderResult:
        native_result = self._native.extract(path)
        if native_result and self._confidence.evaluate(native_result) >= self._threshold:
            return native_result
        return self._extract_pages(path, use_vlm=False)

    def _extract_pages(self, path: Path, use_vlm: bool) -> ProviderResult:
        with self._rasterizer.pages(path) as pages:
            results = [
                self._vlm_router.extract(page) if use_vlm else self._ocr_router.extract(page)
                for page in pages
            ]
        if not results:
            raise ProcessingError("Document contains no processable pages")
        return ProviderResult(
            text="\n\n".join(result.text for result in results),
            confidence=sum(result.confidence for result in results) / len(results),
            provider=results[0].provider,
            page_count=len(results),
        )

    @staticmethod
    def _touch(document: Document) -> None:
        document.updated_at = datetime.now(UTC)
