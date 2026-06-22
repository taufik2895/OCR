from pathlib import Path

from pypdf import PdfReader

from src.providers.base import ProviderResult


class NativeTextExtractionService:
    def extract(self, document: Path) -> ProviderResult | None:
        if document.suffix.lower() != ".pdf":
            return None
        reader = PdfReader(document)
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        text = "\n\n".join(page for page in pages if page)
        if not text:
            return None
        populated_ratio = sum(bool(page) for page in pages) / max(1, len(pages))
        density_score = min(1.0, len(text) / max(1, len(pages) * 500))
        confidence = min(0.99, 0.65 + 0.2 * populated_ratio + 0.14 * density_score)
        return ProviderResult(
            text=text, confidence=confidence, provider="native-pdf", page_count=max(1, len(pages))
        )
