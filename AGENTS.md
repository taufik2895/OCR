# AGENTS.md

## PROJECT

Intelligent Document Processing (IDP) Platform.

Platform membaca dokumen menggunakan native text extraction, OCR tradisional, atau Vision
Language Model (VLM), kemudian mengekstrak field, melakukan resolusi master data, dan membangun
payload generik untuk integrasi masa depan.

Integrasi target belum ditentukan. Jangan mengimplementasikan submission, automation, atau
target-specific transport pada fase saat ini.

---

## SOURCE OF TRUTH

Urutan prioritas dokumen:

1. `AGENTS.md`
2. `PROJECT_SPEC.md`
3. `TASKS.md`

Jika requirement belum terdokumentasi atau bertentangan, catat ketidakpastian sebelum membuat
asumsi atau kode.

---

## DEVELOPMENT PRINCIPLES

Prioritas:

1. Accuracy
2. Maintainability
3. Scalability
4. Performance
5. Cost Efficiency

---

## IMMUTABLE OCR RULE

Dokumen fisik adalah source of truth.

- Simpan OCR text persis seperti output provider.
- Jangan mengubah, menormalisasi, mengoreksi, atau menulis ulang OCR text.
- Jangan mengubah `raw_value` hasil ekstraksi.
- Validation hanya menghasilkan status, warning, atau error terpisah.
- Resolved master data disimpan terpisah dan tidak menggantikan nilai mentah.

---

## REQUIRED PIPELINE

1. Native Text Extraction
2. Traditional OCR
3. Confidence Evaluation
4. VLM OCR fallback
5. Non-mutating Validation
6. Template-driven Field Extraction
7. Master Data Resolution
8. Template-driven Payload Building
9. Export

Jangan menggunakan VLM jika native extraction atau OCR tradisional sudah memenuhi threshold.
Setiap tahap wajib menyimpan provenance dan tidak boleh memutasi output tahap sebelumnya.

---

## PROVIDERS

Traditional OCR:

- PaddleOCR
- Tesseract
- OCRMyPDF

VLM:

- Qwen2.5-VL
- Qwen3-VL
- InternVL
- GPT Vision
- Claude Vision

Provider harus berada di balik interface agar dapat diganti melalui dependency injection.

---

## DYNAMIC TEMPLATES

- Document types, field definitions, resolver rules, dan payload mappings tidak boleh di-hardcode.
- Template harus dapat ditambah atau diubah tanpa perubahan source code.
- Template harus memiliki identifier dan version.
- Template repository harus dapat diganti tanpa mengubah service layer.
- Konfigurasi file fase saat ini menggunakan versioned JSON.

Setiap extracted field wajib memiliki:

```json
{
  "field_name": "...",
  "raw_value": "...",
  "confidence": 0.95,
  "source": "ocr"
}
```

Field yang tidak ditemukan disimpan dengan `raw_value: null`, confidence `0`, dan status terpisah.

---

## MASTER DATA RESOLUTION

Resolver yang didukung secara arsitektural:

- Static JSON
- Database
- External API

Fase saat ini mengimplementasikan Static JSON dan interface untuk adapter masa depan. Matching
harus dikonfigurasi secara eksplisit melalui exact values atau aliases. Jangan melakukan fuzzy
normalization tersembunyi.

Resolution disimpan terpisah dalam bentuk raw value, resolved ID, resolved name, confidence,
resolver name, dan status.

---

## PAYLOAD BUILDER

- Payload dibangun dari mapping template.
- Jangan hardcode field target atau struktur payload.
- Mapping dapat memilih extracted raw value atau resolved ID/name.
- Payload builder tidak mengirim payload ke sistem luar.
- Missing required mapping harus menghasilkan validation error, bukan nilai buatan.

---

## CODING RULES

- Python 3.11+
- FastAPI
- Clean Architecture
- SOLID Principles
- Service Layer Pattern
- Repository Pattern
- Dependency Injection
- Type Hints Required
- Pydantic Models Required
- Structured Logging Required
- Business logic dilarang berada di routers

---

## QUALITY TARGETS

- OCR Accuracy >= 95%
- Structured Extraction >= 90%
- Critical Field Accuracy >= 98%

Target adalah acceptance criteria yang harus diukur dengan benchmark dataset; test unit tidak
boleh mengklaim target tersebut telah tercapai tanpa dataset representatif.

---

## OUT OF SCOPE

- API submission
- SOAP submission
- Desktop automation
- Electron automation
- Windows UI automation
- RPA
- Browser automation

---

## FUTURE FEATURES

- Handwriting OCR
- Signature Detection
- Stamp Detection
- Document Classification
- Database and External API Master Data Resolvers
- Integration Adapters
- RAG Search
- Multi Agent Validation

