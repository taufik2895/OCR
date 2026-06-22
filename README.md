# OCR VLM Platform

FastAPI OCR platform implementing an accuracy-first pipeline:

1. Native PDF text extraction
2. PaddleOCR or Tesseract
3. Confidence evaluation
4. Optional Qwen2.5-VL fallback
5. Validation and structured extraction
6. TXT, JSON, CSV, or XLSX export

## Run locally

Python 3.11 and a Tesseract executable are required for the default lightweight setup.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn src.main:app --reload
```

Open `http://localhost:8000` for the UI or `http://localhost:8000/docs` for Swagger.

Install PaddleOCR support with `python -m pip install -e ".[paddle]"`. Install local Qwen
support with `python -m pip install -e ".[vlm]"`, set `OCR_VLM_ENABLED=true`, and ensure
the host has sufficient GPU memory. Models are loaded lazily on the first fallback request.

## Configuration

All settings use the `OCR_` prefix. See `.env.example` for defaults. Important production
settings are `OCR_DATA_DIR`, `OCR_MAX_UPLOAD_MB`, `OCR_CONFIDENCE_THRESHOLD`,
`OCR_OCR_PROVIDER`, and `OCR_VLM_ENABLED`.

## API workflow

```text
POST /api/v1/documents
POST /api/v1/documents/{id}/process
GET  /api/v1/documents/{id}
GET  /api/v1/documents/{id}/export/{txt|json|csv|xlsx}
GET  /api/v1/documents
GET  /api/v1/dashboard
```

The repository boundary is defined as a protocol. The included atomic JSON implementation is
durable for a single deployment; a database adapter can replace it without changing services.
For multi-instance production deployment, use a shared object store plus a transactional database.

## Quality checks

```powershell
python -m ruff check src
python -m pytest --cov=src
```

## Container

```powershell
docker build -t ocr-vlm-platform .
docker run --rm -p 8000:8000 -v ocr-data:/app/data ocr-vlm-platform
```

The base image includes Tesseract. Build a GPU-specific image with the optional Paddle/Qwen
dependencies when those providers are required.

