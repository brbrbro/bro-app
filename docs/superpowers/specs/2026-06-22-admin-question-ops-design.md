# Admin Question Operations Design

**Date:** 2026-06-22
**Status:** Approved for user review
**Scope:** Web-admin question-bank operations module only. Feedback/errors, user management, and operations dashboard are later phases.

---

## Goal

Build the first phase of the BRO App admin platform as a web-based question-bank operations console.

This phase focuses on:

- Import batch management
- Review queue operations
- Formal question bank management
- Question quality checks
- Recognition/import statistics

The goal is to let admins operate the question lifecycle end-to-end: upload/import, inspect parsed batches, review parsed questions, approve into the official bank, manage existing questions, and monitor quality/recognition results.

---

## Existing Context

The project already has:

- `web-admin` React app using Ant Design
- Existing web-admin pages:
  - `Import`
  - `Review`
  - `QuestionBank`
- Backend import APIs:
  - `/api/import/single`
  - `/api/import/batch`
  - `/api/import/batches`
  - `/api/import/batch/:id`
  - `/api/import/batch/:id/questions`
  - `/api/import/parsed/:id`
  - approve / reject / split / merge / approve-safe
- Backend data models:
  - `ImportBatch`
  - `ParsedQuestion`
  - `Question`
  - `QuestionImage`

This design upgrades and organizes the existing admin app rather than replacing it.

---

## Information Architecture

The web-admin left navigation should introduce a primary module:

```text
题库运营
  - 导入批次
  - 审核队列
  - 题库管理
  - 质量检查
  - 识别统计
```

Later phases will add:

```text
反馈 / 报错
用户管理
运营总览
```

The existing `Import`, `Review`, and `QuestionBank` pages should be treated as the first three pages under `题库运营`.

---

## Page Design

### 1. 导入批次

Purpose: manage all import jobs and quickly understand import progress and failures.

Shows:

- batch id
- source file
- source type
- exam type
- subject
- grade
- knowledge point
- status
- total questions
- parsed questions
- approved questions
- recognition success rate
- low-confidence count
- created time
- failure reason if available

Actions:

- open review queue for a batch
- view batch detail
- delete batch
- reparse batch
- filter by status, subject, file type, date range

### 2. 审核队列

Purpose: review parsed questions and approve them into the formal question bank.

Layout: three-column workspace.

Left:

- batch list
- parsed question list
- confidence indicators
- status filters

Middle:

- original OCR/raw text
- source page number
- associated images
- formula images
- original region/bounding box metadata when available

Right:

- structured editor for content/options/answer/explanation
- subject/grade/knowledge point/type/difficulty
- LaTeX formulas
- associated images

Actions:

- save draft
- approve into `Question`
- reject
- split
- merge with previous/target question
- approve high-confidence questions in batch

### 3. 题库管理

Purpose: manage official questions already in the question bank.

Shows:

- question id
- content preview
- subject
- grade
- knowledge point
- type
- difficulty
- source
- status
- solved count
- correct rate
- created time

Filters:

- subject
- grade
- knowledge point
- question type
- difficulty
- source
- status
- keyword search

Actions:

- view question detail
- edit question
- archive / unarchive
- delete
- jump to related import batch if source is import

### 4. 质量检查

Purpose: surface problematic questions so admins can fix them quickly.

Issue types:

- missing answer
- missing explanation
- choice question with missing/invalid options
- duplicate content
- imported question with low confidence
- question with unknown type
- question with missing subject/knowledge point

Shows:

- issue type
- severity
- question id or parsed question id
- content preview
- suggested action

Actions:

- open editor
- archive/delete
- mark as ignored
- refresh scan

### 5. 识别统计

Purpose: monitor import recognition quality and review throughput.

Metrics:

- total import batches
- total parsed questions
- total approved questions
- approval rate
- average confidence
- low-confidence count
- failed batch count
- average questions per batch

Breakdowns:

- by date
- by subject
- by file type
- by status

Charts can be simple Ant Design tables/cards in the first version. Advanced charting is optional and not required for MVP.

---

## Backend API Design

Admin APIs should live under `/api/admin/...` to separate operational endpoints from regular user APIs.

### Import Batch Management

#### `GET /api/admin/import/batches`

Query params:

- page
- per_page
- status
- subject
- source_type
- start_date
- end_date

Returns paginated batches plus derived fields:

- success_rate
- low_confidence_count
- failure_reason

#### `GET /api/admin/import/batches/:id`

Returns batch detail and summary statistics.

#### `DELETE /api/admin/import/batches/:id`

Deletes an import batch and its parsed questions.

This does not delete already-approved official `Question` rows.

#### `POST /api/admin/import/batches/:id/reparse`

Re-runs recognition on the original source file when `source_url` exists.

If the original file is missing, returns `400` with `source_file_missing`.

### Review Queue

Existing import review APIs remain valid:

- `GET /api/import/batch/:id/questions`
- `PUT /api/import/parsed/:id`
- `POST /api/import/question/:id/approve`
- `POST /api/import/question/:id/reject`
- `POST /api/import/parsed/:id/split`
- `POST /api/import/parsed/:id/merge`
- `POST /api/import/batch/:id/approve-safe`

Admin UI can call these directly in this phase.

### Question Bank Management

#### `GET /api/admin/questions`

Query params:

- page
- per_page
- keyword
- subject
- grade
- knowledge_point
- type
- difficulty
- source
- status

Returns paginated official questions.

#### `GET /api/admin/questions/:id`

Returns full question detail.

#### `PUT /api/admin/questions/:id`

Updates editable fields:

- content
- options
- answer
- explanation
- subject
- grade
- knowledge_point
- type
- difficulty
- status

#### `POST /api/admin/questions/:id/archive`

Sets `status='archived'`.

#### `DELETE /api/admin/questions/:id`

Hard delete. This should be available but visually dangerous in UI.

### Quality Check

#### `GET /api/admin/quality/issues`

Query params:

- issue_type
- severity
- subject
- page
- per_page

Returns issue rows from live queries. No new table is required in the first version.

Issue detection rules:

- `missing_answer`: answer is null/empty
- `missing_explanation`: explanation is null/empty
- `invalid_options`: type is choice and options empty/invalid JSON/fewer than 2 options
- `duplicate_content`: same normalized content appears more than once
- `unknown_type`: type is null/empty/unknown
- `missing_taxonomy`: missing subject or knowledge point
- `low_confidence_import`: ParsedQuestion confidence below threshold and status pending

### Recognition Statistics

#### `GET /api/admin/import/stats`

Query params:

- start_date
- end_date
- group_by: `day`, `subject`, `source_type`, `status`

Returns:

- totals
- rates
- grouped rows

The first version can compute stats directly from `ImportBatch` and `ParsedQuestion` with SQLAlchemy queries.

---

## Data Model Changes

No required new table for MVP.

Optional small additions:

- `ImportBatch.error_message`: store failure reason
- `Question.status` already exists and can support `approved` / `archived`

If `error_message` does not exist, first version may derive failure reason from status and omit detailed traceback. A later plan can add the field if needed.

---

## Frontend API Client

Extend `web-admin/src/services/api.js` with admin methods:

- `getAdminBatches(params)`
- `getAdminBatch(id)`
- `deleteAdminBatch(id)`
- `reparseAdminBatch(id)`
- `getAdminQuestions(params)`
- `getAdminQuestion(id)`
- `updateAdminQuestion(id, data)`
- `archiveAdminQuestion(id)`
- `deleteAdminQuestion(id)`
- `getQualityIssues(params)`
- `getImportStats(params)`

Existing import/review methods should remain.

---

## Frontend Routing

Update `web-admin/src/App.js` to expose routes:

- `/ops/import-batches`
- `/ops/review`
- `/ops/questions`
- `/ops/quality`
- `/ops/stats`

Existing `/`, `/review`, `/bank` routes may redirect or remain as aliases.

---

## Error Handling

Admin APIs should return clear JSON errors:

- `not_found`
- `invalid_params`
- `source_file_missing`
- `delete_failed`
- `reparse_failed`

UI should show Ant Design `message.error(...)` for failures and avoid silent failures.

---

## Testing Strategy

### Backend pytest

Add tests for:

- admin batch list filters
- admin batch detail
- delete batch deletes parsed questions but not official questions
- reparse missing source file returns 400
- question list filters
- question update
- archive question
- delete question
- quality issue detection
- import stats totals and grouping

### Frontend validation

Because web-admin currently has no committed test setup beyond React scripts, first version should at minimum:

- run `npm install` if needed
- run `npm run build`
- manually verify the five routes render

---

## Acceptance Criteria

The first version is complete when:

- web-admin sidebar contains `题库运营` with 5 pages
- admin can view and filter import batches
- admin can open a batch in the review workspace
- admin can search/filter official questions
- admin can edit/archive/delete official questions
- quality page lists at least missing answer, missing explanation, invalid options, duplicate content, unknown type, missing taxonomy, low-confidence import issues
- stats page shows import totals, approval rate, confidence average, failed batches, and grouped rows
- backend tests for all new admin APIs pass
- existing 70 backend tests still pass
- web-admin build succeeds

---

## Out of Scope

- Full admin authentication and role management
- Feedback/error/user/dashboard modules
- Advanced chart library
- CSV export
- Scheduled background quality scans
- Real-time logs

These will be handled in later phases according to the user-defined order: feedback/errors, then users, then dashboard.
