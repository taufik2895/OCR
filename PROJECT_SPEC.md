# PROJECT_SPEC.md

## PROJECT NAME

Intelligent Document Processing Platform

---

## BUSINESS GOAL

Mengekstrak data dari dokumen fisik secara akurat, mempertahankan seluruh nilai mentah, melakukan
resolusi referensi tanpa memutasi hasil OCR, dan menghasilkan payload konfiguratif yang siap
digunakan oleh integration layer di masa depan.

---

## INPUT

Supported:

- PDF
- JPG
- JPEG
- PNG
- TIFF

---

## OUTPUT

Supported:

- TXT
- JSON
- CSV
- XLSX
- Generic payload object

---

## WORKFLOW

```text
User Upload File
  -> Optional Document Template Selection
  -> Native Text Extraction
  -> Traditional OCR when native text is insufficient
  -> Confidence Evaluation
  -> VLM OCR when confidence is below threshold
  -> Non-mutating Validation
  -> Template-driven Field Extraction
  -> Master Data Resolution
  -> Template-driven Payload Building
  -> Export Result
```

Tidak ada tahap yang boleh memodifikasi OCR text atau extracted `raw_value`.

---

## DOCUMENT TEMPLATES

Document type tidak di-hardcode. `HM`, `HGB`, dan `HP` hanya contoh data, bukan enum source code.

Template disimpan sebagai versioned JSON dan dimuat melalui repository. Template baru harus dapat
ditambahkan tanpa perubahan source code. Sebuah template mendefinisikan:

- `template_id`
- `version` as a positive integer; the highest version is the current version
- `display_name`
- field extraction rules
- optional master data resolver references
- optional payload mappings

Pemilihan template saat ini dilakukan secara eksplisit melalui `template_id`. Automatic document
classification tetap future scope sampai aturan atau model klasifikasi terdokumentasi.

---

## FIELD EXTRACTION

Field extraction memakai aturan template. Fase saat ini mendukung strategi deterministik:

- `label`: mengambil nilai setelah label tanpa mengubah karakter hasil tangkapan
- `regex`: mengambil named group `value` atau capture group pertama

Setiap field menghasilkan `field_name`, nullable `raw_value`, confidence, source, dan status.
Confidence field berasal dari confidence OCR dikalikan kualitas kecocokan rule; rumus harus
deterministik dan dapat diuji.

---

## MASTER DATA RESOLUTION

Resolution tidak mengubah extracted field. Hasil resolution adalah object terpisah yang memuat:

- `field_name`
- `raw_value`
- `resolved_id`
- `resolved_name`
- `confidence`
- `resolver`
- `status`

Static JSON resolver memakai exact match dan aliases yang didefinisikan di data master. Database
dan External API disediakan sebagai interface/adapters masa depan dan tidak diimplementasikan pada
scope sekarang.

Matching bersifat case-sensitive. Exact canonical-name match memiliki confidence `1.0`, sedangkan
explicit alias match memiliki confidence `0.97`. Nilai lain tidak diubah dan berstatus unresolved.

---

## PAYLOAD BUILDER

Payload mapping didefinisikan dalam template, tidak di source code. Setiap mapping memuat target
path, source field, value selector (`raw_value`, `resolved_id`, atau `resolved_name`), dan flag
`required`. Target path memakai dot notation untuk nested object.

Payload builder hanya menghasilkan object. Pengiriman ke API, SOAP, desktop, RPA, atau browser
tidak termasuk scope.

---

## STORAGE AND VERSIONING

- Uploaded files dan processing results menggunakan repository boundary.
- Template file berada di configurable template directory.
- Master data file berada di configurable master-data directory.
- Results menyimpan template ID dan version yang digunakan agar dapat diaudit.
- File configuration divalidasi dengan Pydantic ketika dimuat.

---

## API SCOPE

- Upload and OCR processing
- List and retrieve document results
- List and retrieve templates
- Process a document with a selected template
- Build and retrieve generic payload
- Export TXT, JSON, CSV, XLSX

Tidak ada endpoint submission ke sistem target.

---

## ERROR POLICY

- Invalid template/configuration: reject with a validation error.
- Required extracted field missing: retain result and report validation error.
- Resolution not found: retain raw value and report unresolved status.
- Required payload value missing: do not invent a value; report payload validation error.
- Provider unavailable: try the configured fallback sequence and report errors with provenance.

---

## HARDWARE

Minimum:

- RAM 16 GB
- CPU Intel Gen12+ or equivalent

Recommended for local VLM:

- RAM 32 GB
- RTX 3060+ or equivalent supported accelerator

---

## ACCEPTANCE TARGETS

- OCR Accuracy >= 95%
- Structured Extraction >= 90%
- Critical Field Accuracy >= 98%

Pengukuran membutuhkan benchmark dataset terpisah. Target belum dianggap tercapai hanya karena
test aplikasi lulus.
