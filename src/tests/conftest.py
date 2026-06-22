from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_settings
from src.core.config import Settings
from src.main import create_app
from src.repositories.documents import JsonDocumentRepository


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        data_dir=tmp_path,
        templates_dir=tmp_path / "templates",
        master_data_dir=tmp_path / "master_data",
        vlm_enabled=False,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    get_settings.cache_clear()
    app = create_app()
    app.state.repository = JsonDocumentRepository(settings.results_dir)
    from src.repositories.templates import JsonTemplateRepository

    app.state.template_repository = JsonTemplateRepository(settings.templates_dir)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()
