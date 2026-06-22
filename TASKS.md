# TASKS.md

## Phase 1 - Application Foundation

- [x] Create FastAPI project
- [x] Create folder structure
- [x] Configure structured logging
- [x] Configure environment settings
- [x] Create upload endpoint

## Phase 2 - Traditional OCR

- [x] Implement PaddleOCR provider
- [x] Implement Tesseract provider
- [x] Implement OCR router
- [x] Implement native PDF text extraction
- [x] Implement PDF rasterization

## Phase 3 - VLM And Confidence

- [x] Implement Qwen VL provider
- [x] Implement VLM router
- [x] Implement confidence scoring
- [x] Preserve raw OCR output without mutation

## Phase 4 - Existing Output

- [x] Implement baseline structured extraction
- [x] Implement export TXT
- [x] Implement export JSON
- [x] Implement export CSV
- [x] Implement export XLSX

## Phase 5 - Existing User Interface

- [x] Frontend UI
- [x] Dashboard
- [x] History

## Phase 6 - Dynamic Template System

- [x] Define versioned Pydantic template models
- [x] Implement template repository protocol
- [x] Implement JSON template repository
- [x] Add configurable template directory
- [x] Add template list and detail endpoints
- [x] Add template validation tests

## Phase 7 - Dynamic Field Extraction

- [x] Replace baseline extraction with template-driven extraction
- [x] Implement label extraction rule
- [x] Implement regex extraction rule
- [x] Preserve extracted raw values exactly
- [x] Store field confidence, source, and status
- [x] Add extraction tests

## Phase 8 - Master Data Resolution

- [ ] Define resolver protocol and resolution models
- [ ] Implement Static JSON resolver
- [ ] Add configurable master-data directory
- [ ] Preserve raw values during resolution
- [ ] Store resolution provenance and status
- [ ] Add resolver tests

## Phase 9 - Generic Payload Builder

- [ ] Define configuration-driven payload mapping models
- [ ] Implement dot-notation payload builder
- [ ] Support raw value and resolved value selectors
- [ ] Validate required payload mappings
- [ ] Persist template ID and version with processing result
- [ ] Expose payload through result API and exports
- [ ] Add payload builder tests

## Future Phases - Not In Current Scope

- [ ] Database master data resolver
- [ ] External API master data resolver
- [ ] Automatic document classification
- [ ] REST or SOAP submission
- [ ] Desktop, Electron, RPA, or browser automation
