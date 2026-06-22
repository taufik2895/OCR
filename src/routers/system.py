from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_repository
from src.models.document import DocumentStatus
from src.repositories.documents import DocumentRepository
from src.schemas.documents import DashboardResponse

router = APIRouter(tags=["System"])


@router.get("/health", summary="Application health check")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/dashboard", response_model=DashboardResponse, summary="Processing metrics")
def dashboard(
    repository: Annotated[DocumentRepository, Depends(get_repository)],
) -> DashboardResponse:
    documents = repository.list(limit=500)
    scores = [item.result.confidence for item in documents if item.result]
    return DashboardResponse(
        total=len(documents),
        completed=sum(item.status == DocumentStatus.COMPLETED for item in documents),
        failed=sum(item.status == DocumentStatus.FAILED for item in documents),
        average_confidence=round(sum(scores) / len(scores), 4) if scores else 0,
    )
