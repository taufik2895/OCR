from pathlib import Path

from src.models.document import Document, DocumentStatus
from src.providers.base import ProviderResult
from src.providers.tesseract import TesseractProvider
from src.repositories.documents import JsonDocumentRepository
from src.services.confidence import ConfidenceService
from src.services.export import ExportService
from src.services.field_extraction import FieldExtractionService
from src.services.processing import ProcessingService


class FakeNative:
    def __init__(self, result: ProviderResult | None) -> None:
        self.result = result

    def extract(self, document: Path) -> ProviderResult | None:
        return self.result


class FakeRasterizer:
    class Context:
        def __init__(self, path: Path) -> None:
            self.path = path

        def __enter__(self) -> list[Path]:
            return [self.path]

        def __exit__(self, *args: object) -> None:
            return None

    def pages(self, document: Path) -> "FakeRasterizer.Context":
        return self.Context(document)


class FakeRouter:
    def __init__(self, result: ProviderResult) -> None:
        self.result = result
        self.calls = 0

    def extract(self, document: Path) -> ProviderResult:
        self.calls += 1
        return self.result


class FakeValidator:
    def validate(self, text: str) -> list[str]:
        return []


class FakeTemplates:
    def get(self, template_id: str, version: int | None = None) -> None:
        return None


def make_document(path: Path) -> Document:
    path.write_text("placeholder", encoding="utf-8")
    return Document(
        original_name=path.name,
        content_type="image/png",
        size_bytes=11,
        checksum_sha256="0" * 64,
        storage_path=path,
    )


def test_confidence_is_bounded() -> None:
    service = ConfidenceService()
    score = service.evaluate(
        ProviderResult(text="Invoice number 123 total 500", confidence=0.95, provider="fake")
    )
    assert 0.8 <= score <= 1
    assert service.evaluate(ProviderResult(text="", confidence=1, provider="fake")) == 0


def test_tesseract_accepts_an_explicit_executable(tmp_path: Path) -> None:
    executable = tmp_path / "tesseract.exe"
    executable.touch()
    provider = TesseractProvider(str(executable))
    assert provider.is_available()


def test_pipeline_uses_native_text_before_ocr(tmp_path: Path) -> None:
    repository = JsonDocumentRepository(tmp_path / "results")
    document = repository.save(make_document(tmp_path / "doc.pdf"))
    native = ProviderResult(
        text="A complete native document " * 30, confidence=0.99, provider="native-pdf"
    )
    ocr = FakeRouter(ProviderResult(text="ocr", confidence=0.9, provider="ocr"))
    vlm = FakeRouter(ProviderResult(text="vlm", confidence=0.9, provider="vlm"))
    service = ProcessingService(
        repository,
        FakeNative(native),
        FakeRasterizer(),
        ocr,
        vlm,
        ConfidenceService(),
        FakeValidator(),
        FakeTemplates(),
        FieldExtractionService(),
        0.85,
    )
    result = service.process(document.id, None, None)
    assert result.status == DocumentStatus.COMPLETED
    assert result.result and result.result.provider == "native-pdf"
    assert ocr.calls == 0
    assert vlm.calls == 0


def test_pipeline_falls_back_to_vlm(tmp_path: Path) -> None:
    repository = JsonDocumentRepository(tmp_path / "results")
    document = repository.save(make_document(tmp_path / "doc.png"))
    ocr = FakeRouter(ProviderResult(text="x", confidence=0.1, provider="ocr"))
    vlm = FakeRouter(
        ProviderResult(text="High quality recognized text " * 10, confidence=0.98, provider="vlm")
    )
    service = ProcessingService(
        repository,
        FakeNative(None),
        FakeRasterizer(),
        ocr,
        vlm,
        ConfidenceService(),
        FakeValidator(),
        FakeTemplates(),
        FieldExtractionService(),
        0.85,
    )
    result = service.process(document.id, None, None)
    assert result.result and result.result.used_vlm is True
    assert result.result.provider == "vlm"


def test_exports_json_csv_and_xlsx(tmp_path: Path) -> None:
    document = make_document(tmp_path / "doc.png")
    from src.models.document import OCRResult

    document.result = OCRResult(text="Name: Ada", confidence=0.98, provider="fake")
    service = ExportService()
    for output_format in ("txt", "json", "csv", "xlsx"):
        content, media_type = service.export(document, output_format)
        assert content
        assert media_type
