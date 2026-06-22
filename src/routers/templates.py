from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_template_repository
from src.core.exceptions import TemplateNotFoundError
from src.models.templates import DocumentTemplate, TemplateSummary
from src.repositories.templates import TemplateRepository

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=list[TemplateSummary], summary="List current templates")
def list_templates(
    repository: Annotated[TemplateRepository, Depends(get_template_repository)],
) -> list[TemplateSummary]:
    return repository.list()


@router.get("/{template_id}", response_model=DocumentTemplate, summary="Get a template")
def get_template(
    template_id: str,
    repository: Annotated[TemplateRepository, Depends(get_template_repository)],
    version: Annotated[int | None, Query(gt=0)] = None,
) -> DocumentTemplate:
    template = repository.get(template_id, version)
    if template is None:
        raise TemplateNotFoundError("Document template not found")
    return template
