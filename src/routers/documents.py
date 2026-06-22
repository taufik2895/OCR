import asyncio
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response

from src.api.dependencies import (
    get_export_service,
    get_processing_service,
    get_repository,
    get_upload_service,
)
from src.core.exceptions import DocumentNotFoundError
from src.models.document import Document
from src.repositories.documents import DocumentRepository
from src.schemas.documents import DocumentSummary, ProcessRequest, ResultResponse, UploadResponse
from src.services.export import ExportService
from src.services.processing import ProcessingService
from src.services.upload import UploadService

router = APIRouter(prefix="/documents", tags=["Documents"])


def _result_response(document: Document) -> ResultResponse:
    result = document.result
    return ResultResponse(
        document_id=document.id,
        filename=document.original_name,
        status=document.status,
        text=result.text if result else "",
        confidence=result.confidence if result else None,
        provider=result.provider if result else None,
        used_vlm=result.used_vlm if result else False,
        template_id=result.template_id if result else None,
        template_version=result.template_version if result else None,
        extracted_fields=list(result.extracted_fields) if result else [],
        extraction_errors=list(result.extraction_errors) if result else [],
        resolutions=list(result.resolutions) if result else [],
        warnings=result.warnings if result else [],
        error=document.error,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF, JPG, JPEG, PNG, or TIFF document")],
    service: Annotated[UploadService, Depends(get_upload_service)],
) -> UploadResponse:
    document = await service.upload(file)
    return UploadResponse(
        id=document.id,
        filename=document.original_name,
        status=document.status,
        size_bytes=document.size_bytes,
    )


@router.post(
    "/{document_id}/process", response_model=ResultResponse, summary="Run the OCR pipeline"
)
async def process_document(
    document_id: UUID,
    request: ProcessRequest,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
) -> ResultResponse:
    document = await asyncio.to_thread(
        service.process,
        document_id,
        request.template_id,
        request.template_version,
        request.force,
    )
    return _result_response(document)


@router.get("/{document_id}", response_model=ResultResponse, summary="Get an OCR result")
def get_document(
    document_id: UUID,
    repository: Annotated[DocumentRepository, Depends(get_repository)],
) -> ResultResponse:
    document = repository.get(document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found")
    return _result_response(document)


@router.get("", response_model=list[DocumentSummary], summary="List processing history")
def list_documents(
    repository: Annotated[DocumentRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[DocumentSummary]:
    return [
        DocumentSummary(
            id=document.id,
            filename=document.original_name,
            status=document.status,
            confidence=document.result.confidence if document.result else None,
            provider=document.result.provider if document.result else None,
            created_at=document.created_at,
        )
        for document in repository.list(limit)
    ]


@router.get("/{document_id}/export/{output_format}", summary="Export an OCR result")
def export_document(
    document_id: UUID,
    output_format: Literal["txt", "json", "csv", "xlsx"],
    repository: Annotated[DocumentRepository, Depends(get_repository)],
    service: Annotated[ExportService, Depends(get_export_service)],
) -> Response:
    document = repository.get(document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found")
    content, media_type = service.export(document, output_format)
    stem = Path(document.original_name).stem
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{stem}.{output_format}"'},
    )
