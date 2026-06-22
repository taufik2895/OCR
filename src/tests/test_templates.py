import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.core.exceptions import ConfigurationError
from src.models.templates import DocumentTemplate
from src.repositories.templates import JsonTemplateRepository


def template_data(version: int = 1) -> dict[str, object]:
    return {
        "schema_version": 1,
        "template_id": "sample",
        "version": version,
        "display_name": "Sample",
        "fields": [
            {
                "field_name": "owner_name",
                "required": True,
                "rule": {"strategy": "label", "label": "Owner"},
            }
        ],
        "payload_mappings": [
            {
                "target_path": "owner.name",
                "source_field": "owner_name",
                "value_selector": "raw_value",
            }
        ],
    }


def write_template(directory: Path, name: str, version: int) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(template_data(version)), encoding="utf-8")


def test_template_model_rejects_unknown_payload_field() -> None:
    data = template_data()
    mappings = data["payload_mappings"]
    assert isinstance(mappings, list)
    mappings[0]["source_field"] = "missing"
    with pytest.raises(ValueError, match="unknown fields"):
        DocumentTemplate.model_validate(data)


def test_repository_returns_latest_or_requested_version(tmp_path: Path) -> None:
    write_template(tmp_path, "sample-v1.json", 1)
    write_template(tmp_path, "sample-v2.json", 2)
    repository = JsonTemplateRepository(tmp_path)
    assert repository.get("sample").version == 2  # type: ignore[union-attr]
    assert repository.get("sample", 1).version == 1  # type: ignore[union-attr]
    assert repository.list()[0].version == 2


def test_repository_rejects_invalid_configuration(tmp_path: Path) -> None:
    (tmp_path / "invalid.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid template"):
        JsonTemplateRepository(tmp_path).list()


def test_template_endpoints(client: TestClient, settings: object) -> None:
    directory = client.app.state.template_repository._directory
    write_template(directory, "sample-v1.json", 1)
    response = client.get("/api/v1/templates")
    assert response.status_code == 200
    assert response.json()[0]["template_id"] == "sample"
    assert client.get("/api/v1/templates/sample").status_code == 200
    assert client.get("/api/v1/templates/missing").status_code == 404
