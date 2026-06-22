import importlib.util
import threading
from pathlib import Path
from typing import Any

from src.core.exceptions import ProcessingError, ProviderUnavailableError
from src.providers.base import ProviderResult


class PaddleOCRProvider:
    name = "paddleocr"

    def __init__(self, language: str = "en") -> None:
        self._language = language
        self._engine: Any = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return importlib.util.find_spec("paddleocr") is not None

    def _get_engine(self) -> Any:
        if not self.is_available():
            raise ProviderUnavailableError("PaddleOCR optional dependencies are not installed")
        with self._lock:
            if self._engine is None:
                from paddleocr import PaddleOCR

                self._engine = PaddleOCR(use_angle_cls=True, lang=self._language, show_log=False)
        return self._engine

    def extract(self, document: Path) -> ProviderResult:
        try:
            output = self._get_engine().ocr(str(document), cls=True)
            lines: list[str] = []
            scores: list[float] = []
            for page in output or []:
                for line in page or []:
                    if len(line) >= 2 and len(line[1]) >= 2:
                        lines.append(str(line[1][0]))
                        scores.append(float(line[1][1]))
            return ProviderResult(
                text="\n".join(lines),
                confidence=sum(scores) / len(scores) if scores else 0,
                provider=self.name,
                page_count=max(1, len(output or [])),
            )
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProcessingError(f"PaddleOCR failed: {exc}") from exc
