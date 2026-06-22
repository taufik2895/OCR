import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pypdfium2 as pdfium


class RasterizationService:
    @contextmanager
    def pages(self, document: Path) -> Iterator[list[Path]]:
        if document.suffix.lower() != ".pdf":
            yield [document]
            return
        with tempfile.TemporaryDirectory(prefix="ocr-pages-") as directory:
            pdf = pdfium.PdfDocument(document)
            paths: list[Path] = []
            try:
                for index, page in enumerate(pdf):
                    target = Path(directory) / f"page-{index + 1}.png"
                    page.render(scale=2.5).to_pil().convert("RGB").save(target, "PNG")
                    paths.append(target)
                yield paths
            finally:
                pdf.close()
