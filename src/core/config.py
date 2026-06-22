from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="OCR_", case_sensitive=False, extra="ignore"
    )

    app_name: str = "OCR VLM Platform"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    data_dir: Path = Path("data")
    templates_dir: Path = Path("config/templates")
    master_data_dir: Path = Path("config/master_data")
    max_upload_mb: int = Field(default=25, ge=1, le=500)
    confidence_threshold: float = Field(default=0.85, ge=0, le=1)
    ocr_provider: Literal["auto", "paddleocr", "tesseract"] = "auto"
    vlm_enabled: bool = False
    qwen_model_id: str = "Qwen/Qwen2.5-VL-3B-Instruct"
    tesseract_cmd: str | None = None

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"


@lru_cache
def get_settings() -> Settings:
    return Settings()
