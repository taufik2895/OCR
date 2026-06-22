import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.dependencies import (
    build_master_data_repository,
    build_repository,
    build_template_repository,
)
from src.core.config import get_settings
from src.core.exceptions import (
    DocumentNotFoundError,
    InvalidDocumentError,
    PlatformError,
    TemplateNotFoundError,
)
from src.core.logging import configure_logging
from src.routers.documents import router as documents_router
from src.routers.system import router as system_router
from src.routers.templates import router as templates_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        settings.results_dir.mkdir(parents=True, exist_ok=True)
        settings.templates_dir.mkdir(parents=True, exist_ok=True)
        settings.master_data_dir.mkdir(parents=True, exist_ok=True)
        logging.getLogger(__name__).info(
            "application_started", extra={"environment": settings.environment}
        )
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Accuracy-first OCR API with traditional OCR and optional VLM fallback.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.repository = build_repository()
    app.state.template_repository = build_template_repository()
    app.state.master_data_repository = build_master_data_repository()
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(templates_router, prefix="/api/v1")

    @app.exception_handler(DocumentNotFoundError)
    @app.exception_handler(TemplateNotFoundError)
    async def not_found_handler(
        request: Request, exc: DocumentNotFoundError | TemplateNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(InvalidDocumentError)
    async def invalid_handler(request: Request, exc: InvalidDocumentError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)}
        )

    @app.exception_handler(PlatformError)
    async def platform_handler(request: Request, exc: PlatformError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)}
        )

    static_dir = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return app


app = create_app()
