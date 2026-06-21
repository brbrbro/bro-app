# Question Import Recognition Design

**Date:** 2026-06-21
**Status:** Draft approved for user review
**Scope:** Web-admin first; mini-program full workflow out of scope for this phase

---

## Goal

Build a high-accuracy question import system for BRO App that supports:

- Single-question import
- Batch paper import
- PDF, Word, image, and plain text sources
- Text, formula, symbol, embedded image, and OCR recognition
- Formula output as editable LaTeX with original formula image fallback
- Automatic association of question diagrams/images to the correct parsed question
- Mandatory human review in web-admin before questions enter the official question bank

---

## Existing Context

The project already has a basic import pipeline:

- `backend/routes/import.py`
  - `POST /api/import/upload`
  - batch status/list/questions endpoints
  - approve/reject endpoints
- `backend/services/file_processor.py`
  - PDF/Word/image/TXT extraction
- `backend/services/ai_parser.py`
  - text parsing with OpenAI fallback
  - simple regex fallback parser
- Existing models:
  - `ImportBatch`
  - `ParsedQuestion`
  - `Question`
  - `QuestionImage`
- Existing web-admin pages:
  - import page
  - review page
  - question bank page

The new design enhances this existing foundation instead of replacing it.

---

## Product Decisions

### Recognition Approach

Use a hybrid recognition pipeline:

1. Local parsing/OCR first for low cost and speed
2. Multimodal AI fallback for low-confidence, formula-heavy, diagram-heavy, or layout-complex questions
3. Human review required before final insertion into `Question`

### Primary UI

Build the complete workflow in web-admin first.

The mini-program can keep a lightweight user-facing submit/upload entry, but full review, correction, split, merge, and approval workflows belong in web-admin.

### Review Policy

All parsed results go into `ParsedQuestion` with status `pending` or equivalent review state. No parsed question is inserted into the official `Question` table until an admin approves it.

### Formula Handling

Formula recognition stores both:

- Editable LaTeX
- Original cropped formula image for fallback and manual correction

### Image Handling

Images, diagrams, charts, and geometry figures should be automatically associated with the nearest/most likely question. Admins can adjust image associations during review.

---

## Architecture

The import system is a pipeline:

```text
Upload
  → DocumentIngestor
  → QuestionSegmenter
  → RecognitionPipeline
  → QuestionNormalizer
  → ParsedQuestion Review Queue
  → Web-admin Review
  → Approved Question
```

### Components

#### DocumentIngestor

Responsible for converting raw files into page-level structured data.

Inputs:

- PDF
- Word `.doc/.docx`
- Image `.jpg/.jpeg/.png`
- Plain text `.txt`

Outputs:

- Page text
- Page images
- Embedded images
- Text blocks with coordinates where available
- Original page screenshots where available

#### QuestionSegmenter

Responsible for splitting page content into question candidates.

Signals:

- Numbered question patterns
- Option labels like A/B/C/D
- Answer/解析 markers
- Layout gaps and indentation
- Nearby image positions
- Page boundaries

Outputs:

- Candidate questions
- Source page number
- Bounding box if available
- Nearby image candidates
- Split confidence

#### RecognitionPipeline

Responsible for improving and validating each candidate.

Local passes:

- OCR for image regions
- Formula region recognition
- Option extraction
- Answer/explanation extraction

AI fallback triggers:

- Low OCR confidence
- Missing options/answer where expected
- Formula-heavy content
- Diagram-heavy content
- Ambiguous split boundaries
- Very noisy OCR text

AI output must follow a strict JSON schema.

#### QuestionNormalizer

Responsible for converting local/AI recognition results into canonical `ParsedQuestion` data.

Canonical fields:

- content
- options
- answer
- explanation
- type
- difficulty
- subject
- grade
- knowledge_point
- source_page
- bbox
- images
- formula_latex
- formula_images
- raw_ocr_text
- confidence
- confidence_detail

---

## Data Model Enhancements

Extend `ParsedQuestion` with:

- `source_page`: integer page number
- `bbox`: JSON bounding box for question region
- `raw_ocr_text`: raw OCR text before cleanup
- `formula_latex`: JSON array of LaTeX snippets
- `formula_images`: JSON array of cropped formula image URLs
- `confidence_detail`: JSON object describing text/formula/layout/image confidence
- `images`: already exists; use it for question-associated images

Use or extend `QuestionImage` for:

- original page screenshots
- embedded question images
- cropped formula images
- processed/normalized image variants
- OCR text attached to each image

`ImportBatch` should track:

- uploaded
- processing
- reviewing
- completed
- failed

The existing `status` field can store these values.

---

## API Design

### Import

#### `POST /api/import/single`

Single-question import.

Supports:

- text-only body
- image upload
- text + image

Returns:

- batch id
- parsed question id
- parsed preview
- confidence details

#### `POST /api/import/batch`

Batch paper import.

Supports:

- PDF
- Word
- image
- TXT

Returns:

- batch id
- status `processing` or `reviewing`
- parsed question count if available synchronously

### Batch Status

#### `GET /api/import/batches`

List import batches with status, source, subject, grade, question counts, and timestamps.

#### `GET /api/import/batch/:id`

Batch detail and processing summary.

#### `GET /api/import/batch/:id/questions`

List parsed questions for review.

### Review Actions

#### `PUT /api/import/parsed/:id`

Save edited parsed question.

Editable fields:

- content
- options
- answer
- explanation
- type
- subject
- grade
- knowledge_point
- difficulty
- formula_latex
- images

#### `POST /api/import/parsed/:id/approve`

Approve parsed question and create official `Question`.

#### `POST /api/import/parsed/:id/reject`

Reject parsed question with optional reason.

#### `POST /api/import/parsed/:id/split`

Split one parsed question into two parsed questions.

#### `POST /api/import/parsed/:id/merge`

Merge a parsed question into the previous or specified parsed question.

#### `POST /api/import/batch/:id/approve-safe`

Batch-approve high-confidence questions after admin confirmation.

This still requires an explicit admin action.

---

## Web-Admin Review UI

The review page uses a three-column layout.

### Left Column: Question List

Shows:

- question index
- status
- confidence score
- warning indicators
- page number
- type

Actions:

- select question
- filter by status
- filter by low confidence
- jump to first error

### Middle Column: Source Preview

Shows:

- original page screenshot
- highlighted question bounding box
- associated images/diagrams
- formula crops
- raw OCR text toggle

Actions:

- zoom
- switch page
- view associated image
- detach/attach image to current question

### Right Column: Structured Editor

Editable fields:

- question content
- options
- answer
- explanation
- formula LaTeX
- subject
- grade
- knowledge point
- difficulty
- type
- associated images

Actions:

- save draft
- approve and insert into question bank
- reject
- split question
- merge with previous question
- preview final rendering

### Batch Actions

- approve all high-confidence questions
- save all edits
- export error list
- refresh recognition result

---

## Recognition Flow Details

### PDF

1. Extract text and coordinates with PyMuPDF
2. Render page screenshot
3. Extract embedded images
4. Run layout segmentation
5. Run OCR on image regions if needed
6. Associate nearby images with question candidates

### Word

1. Extract paragraphs and tables
2. Extract embedded images
3. Convert OMML/math where possible to LaTeX
4. Preserve image references
5. Segment by numbered questions and option labels

### Image

1. Store original image
2. OCR full image
3. Detect question blocks and formula/image regions
4. Run formula recognition or AI fallback
5. Produce one or multiple question candidates depending on segmentation

### TXT

1. Parse numbered questions
2. Detect options, answers, explanations
3. Skip OCR and image handling

---

## Error Handling

### Upload Errors

- unsupported file type
- missing subject/exam type
- empty file
- file too large

### Recognition Errors

- no questions detected
- OCR failed
- AI unavailable
- malformed AI JSON
- formula recognition failed

### Review Errors

- missing required fields before approval
- invalid options JSON
- empty answer where required
- image URL missing

Failed recognition should not lose the batch. The batch should move to `reviewing` or `failed` with error detail, and any partially parsed questions should remain reviewable.

---

## Testing Strategy

### Unit Tests

- document ingestion for TXT/PDF fixture
- numbered question segmentation
- option parsing
- answer/explanation parsing
- formula field persistence
- image association metadata persistence
- AI JSON schema validation

### API Tests

- single text import creates one `ParsedQuestion`
- batch text import creates multiple `ParsedQuestion` rows
- unsupported file rejected
- missing subject rejected
- approve parsed question creates `Question`
- reject updates status
- split creates an extra parsed question
- merge combines content and marks source row merged/rejected

### Web-Admin Tests / Manual QA

- upload file from import page
- open batch review page
- edit fields
- save draft
- approve question
- reject question
- split and merge questions
- view original screenshot and associated images

### Recognition Acceptance

First version target:

- normal text questions: at least 90% field-level accuracy on clean input
- formulas: editable LaTeX present when recognized; original formula image retained regardless
- diagrams/images: at least attached to the likely question; admin can adjust manually
- batch paper: most numbered questions split correctly, with manual correction available

---

## Out of Scope

- Excel/CSV import
- automatic no-review publishing
- full mini-program review interface
- asynchronous queue with Celery/RQ
- production-grade OCR model deployment tuning
- guaranteed perfect formula recognition

---

## Implementation Notes

The first implementation plan should prioritize:

1. Data model enhancements and migrations
2. Backend recognition pipeline interfaces
3. TXT single and batch import path as a deterministic baseline
4. PDF/Word/image ingestion improvements
5. AI fallback contract and schema validation
6. Web-admin review UI
7. Approval/split/merge APIs
8. End-to-end tests

This order creates a working vertical slice early and reduces risk before advanced OCR/AI recognition is layered in.
