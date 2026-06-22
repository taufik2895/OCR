from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from src.core.config import Settings, get_settings
from src.providers.base import OCRProvider
from src.providers.paddleocr import PaddleOCRProvider
from src.providers.tesseract import TesseractProvider
from src.providers.vlm import QwenVLProvider
from src.repositories.documents import DocumentRepository, JsonDocumentRepository
from src.repositories.master_data import JsonMasterDataRepository, MasterDataRepository
from src.repositories.templates import JsonTemplateRepository, TemplateRepository
from src.services.confidence import ConfidenceService
from src.services.export import ExportService
from src.services.field_extraction import FieldExtractionService
from src.services.master_data import MasterDataResolutionService, StaticJsonResolver
from src.services.native_extraction import NativeTextExtractionService
from src.services.ocr_router import OCRRouterService
from src.services.processing import ProcessingService
from src.services.rasterization import RasterizationService
from src.services.upload import UploadService
from src.services.validation import ValidationService
from src.services.vlm_router import VLMRouterService


@lru_cache
def build_repository() -> JsonDocumentRepository:
    return JsonDocumentRepository(get_settings().results_dir)


@lru_cache
def build_template_repository() -> JsonTemplateRepository:
    return JsonTemplateRepository(get_settings().templates_dir)


@lru_cache
def build_master_data_repository() -> JsonMasterDataRepository:
    return JsonMasterDataRepository(get_settings().master_data_dir)


def build_ocr_providers(settings: Settings) -> list[OCRProvider]:
    providers: dict[str, OCRProvider] = {
        "paddleocr": PaddleOCRProvider(),
        "tesseract": TesseractProvider(settings.tesseract_cmd),
    }
    if settings.ocr_provider == "auto":
        return [providers["paddleocr"], providers["tesseract"]]
    return [providers[settings.ocr_provider]]


def get_repository(request: Request) -> DocumentRepository:
    return request.app.state.repository


def get_template_repository(request: Request) -> TemplateRepository:
    return request.app.state.template_repository


def get_master_data_repository(request: Request) -> MasterDataRepository:
    return request.app.state.master_data_repository


def get_upload_service(
    repository: Annotated[DocumentRepository, Depends(get_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadService:
    return UploadService(repository, settings.uploads_dir, settings.max_upload_mb * 1024 * 1024)


def get_processing_service(
    repository: Annotated[DocumentRepository, Depends(get_repository)],
    templates: Annotated[TemplateRepository, Depends(get_template_repository)],
    master_repository: Annotated[MasterDataRepository, Depends(get_master_data_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProcessingService:
    return ProcessingService(
        repository=repository,
        native=NativeTextExtractionService(),
        rasterizer=RasterizationService(),
        ocr_router=OCRRouterService(build_ocr_providers(settings)),
        vlm_router=VLMRouterService([QwenVLProvider(settings.qwen_model_id)], settings.vlm_enabled),
        confidence=ConfidenceService(),
        validator=ValidationService(),
        templates=templates,
        field_extractor=FieldExtractionService(),
        master_data=MasterDataResolutionService([StaticJsonResolver(master_repository)]),
        threshold=settings.confidence_threshold,
    )


def get_export_service() -> ExportService:
    return ExportService()
