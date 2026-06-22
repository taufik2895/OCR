import hashlib
import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.core.exceptions import InvalidDocumentError
from src.models.document import Document
from src.repositories.documents import DocumentRepository


class UploadService:
    _allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    _allowed_types = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
    }

    def __init__(self, repository: DocumentRepository, uploads_dir: Path, max_bytes: int) -> None:
        self._repository = repository
        self._uploads_dir = uploads_dir
        self._max_bytes = max_bytes
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, upload: UploadFile) -> Document:
        filename = Path(upload.filename or "").name
        extension = Path(filename).suffix.lower()
        if not filename or extension not in self._allowed_extensions:
            raise InvalidDocumentError("Unsupported file extension")
        if upload.content_type not in self._allowed_types:
            raise InvalidDocumentError("Unsupported content type")

        safe_stem = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).stem)[:80] or "document"
        target = self._uploads_dir / f"{uuid4()}-{safe_stem}{extension}"
        digest = hashlib.sha256()
        size = 0
        try:
            with target.open("wb") as stream:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > self._max_bytes:
                        raise InvalidDocumentError("File exceeds configured upload limit")
                    digest.update(chunk)
                    stream.write(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

        if size == 0:
            target.unlink(missing_ok=True)
            raise InvalidDocumentError("Empty files are not accepted")

        document = Document(
            original_name=filename,
            content_type=upload.content_type or "application/octet-stream",
            size_bytes=size,
            checksum_sha256=digest.hexdigest(),
            storage_path=target,
        )
        return self._repository.save(document)
