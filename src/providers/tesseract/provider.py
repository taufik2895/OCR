import shutil
import sys
from pathlib import Path

import pytesseract
from PIL import Image
from pytesseract import Output

from src.core.exceptions import ProcessingError, ProviderUnavailableError
from src.providers.base import ProviderResult


class TesseractProvider:
    name = "tesseract"

    def __init__(self, command: str | None = None, language: str = "eng") -> None:
        self._command = self._resolve_command(command)
        self._language = language
        if self._command:
            pytesseract.pytesseract.tesseract_cmd = self._command

    def is_available(self) -> bool:
        return self._command is not None

    @staticmethod
    def _resolve_command(command: str | None) -> str | None:
        if command and Path(command).is_file():
            return command
        discovered = shutil.which("tesseract")
        if discovered:
            return discovered
        if sys.platform == "win32":
            candidates = (
                Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
                Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
                Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe",
            )
            return next((str(path) for path in candidates if path.is_file()), None)
        return None

    def extract(self, document: Path) -> ProviderResult:
        if not self.is_available():
            raise ProviderUnavailableError("Tesseract executable is not available")
        if document.suffix.lower() == ".pdf":
            raise ProcessingError("Tesseract PDF processing requires prior rasterization")
        try:
            with Image.open(document) as image:
                data = pytesseract.image_to_data(
                    image, lang=self._language, output_type=Output.DICT
                )
                words: list[str] = []
                confidences: list[float] = []
                for text, confidence in zip(data["text"], data["conf"], strict=True):
                    if text.strip() and float(confidence) >= 0:
                        words.append(text.strip())
                        confidences.append(float(confidence) / 100)
                return ProviderResult(
                    text=" ".join(words),
                    confidence=sum(confidences) / len(confidences) if confidences else 0,
                    provider=self.name,
                    page_count=getattr(image, "n_frames", 1),
                )
        except Exception as exc:
            raise ProcessingError(f"Tesseract failed: {exc}") from exc
