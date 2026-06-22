import json
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from src.core.exceptions import ConfigurationError
from src.models.master_data import MasterDataSet


class MasterDataRepository(Protocol):
    def get(self, dataset_id: str) -> MasterDataSet | None: ...


class JsonMasterDataRepository:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def get(self, dataset_id: str) -> MasterDataSet | None:
        matches: list[MasterDataSet] = []
        for path in sorted(self._directory.glob("*.json")):
            try:
                dataset = MasterDataSet.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, ValidationError) as exc:
                raise ConfigurationError(f"Invalid master data {path.name}: {exc}") from exc
            if dataset.dataset_id == dataset_id:
                matches.append(dataset)
        if len(matches) > 1:
            raise ConfigurationError(f"Duplicate master data dataset '{dataset_id}'")
        return matches[0] if matches else None
