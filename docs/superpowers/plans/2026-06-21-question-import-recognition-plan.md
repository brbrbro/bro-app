# Question Import Recognition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-admin-first question import system that supports single-question and batch-paper import with hybrid local/AI recognition, LaTeX+image formula fallback, per-question image association, and mandatory human review before final question-bank insertion.

**Architecture:** Extend the existing `ImportBatch` / `ParsedQuestion` / `QuestionImage` pipeline instead of replacing it. Add focused backend services (`DocumentIngestor`, `QuestionSegmenter`, `RecognitionPipeline`, `QuestionNormalizer`) and new review APIs; improve web-admin into a three-column review workspace. Use deterministic local parsing as the baseline, with OCR/AI hooks isolated behind interfaces so tests do not require external APIs.

**Tech Stack:** Flask 3.0 / SQLAlchemy / PyMuPDF / mammoth / Pillow / pytesseract / OpenAI SDK / pytest / React 18 / Ant Design 5 / axios

---

## Scope and Constraints

### In Scope

- Single-question import via text, image, or text+image.
- Batch import via PDF, Word, image, and TXT.
- Recognition pipeline with local extraction first and AI fallback hooks.
- Formula output as LaTeX plus original formula image fallback.
- Question-associated images stored and exposed for review.
- Web-admin review UI with list, source preview, and structured editor.
- Parsed questions require admin approval before insertion into `Question`.
- Tests for backend services and API endpoints.

### Out of Scope

- Excel/CSV import.
- Fully automated no-review publishing.
- Production Celery/RQ background queue.
- Full mini-program review UI.
- Guaranteed perfect formula recognition.
- Paid OCR/AI provider tuning.

---

## File Structure

```text
backend/
├── models.py                                Modify: enhance ParsedQuestion metadata
├── migrate_import_recognition.py            Create: SQLite migration for new columns
├── routes/
│   └── import.py                            Modify: new single/batch/review/split/merge APIs
├── services/
│   ├── import_schema.py                     Create: canonical dataclasses/helpers
│   ├── document_ingestor.py                 Create: file-to-page extraction
│   ├── question_segmenter.py                Create: deterministic question splitting
│   ├── recognition_pipeline.py              Create: local+AI recognition orchestration
│   ├── question_normalizer.py               Create: candidate-to-ParsedQuestion conversion
│   ├── ai_json.py                           Create: strict AI JSON parsing/repair
│   └── formula_utils.py                     Create: LaTeX/formula image helpers
└── tests/
    ├── test_import_schema.py                Create
    ├── test_document_ingestor.py            Create
    ├── test_question_segmenter.py           Create
    ├── test_recognition_pipeline.py         Create
    ├── test_import_api_single_batch.py      Create
    └── test_import_review_actions.py        Create

web-admin/
└── src/
    ├── services/api.js                      Modify: new import/review API methods
    └── pages/
        ├── Import/Import.js                 Modify: single/batch mode upload
        ├── Import/Import.css                Modify
        ├── Review/Review.js                 Replace: three-column review workspace
        └── Review/Review.css                Replace
```

---

## Phase 1: Backend Data Model and Migration

### Task 1: Add import recognition metadata columns

**Files:**
- Modify: `backend/models.py`
- Create: `backend/migrate_import_recognition.py`
- Test: `backend/tests/test_import_schema.py`

- [ ] **Step 1: Write failing model metadata test**

Create `backend/tests/test_import_schema.py`:

```python
import json


def test_parsed_question_supports_recognition_metadata(client, app):
    from models import db, ParsedQuestion

    with app.app_context():
        pq = ParsedQuestion(
            batch_id=1,
            raw_content='{}',
            content='已知 $x^2=4$，求 x。',
            options='[]',
            answer='±2',
            explanation='平方根定义',
            exam_type='gaokao',
            subject='数学',
            grade='高一',
            knowledge_point='方程',
            type='blank',
            difficulty=2,
            status='pending',
            source_page=1,
            bbox=json.dumps({'x': 10, 'y': 20, 'w': 300, 'h': 160}),
            raw_ocr_text='1. 已知 x^2=4，求 x。',
            formula_latex=json.dumps(['x^2=4']),
            formula_images=json.dumps(['/static/images/formula-1.png']),
            confidence_detail=json.dumps({'text': 0.96, 'formula': 0.82, 'layout': 0.9})
        )
        db.session.add(pq)
        db.session.commit()

        saved = ParsedQuestion.query.first()
        assert saved.source_page == 1
        assert json.loads(saved.bbox)['w'] == 300
        assert json.loads(saved.formula_latex) == ['x^2=4']
        assert json.loads(saved.confidence_detail)['formula'] == 0.82
```

- [ ] **Step 2: Run failing test**

Run from `backend`:

```powershell
pytest tests/test_import_schema.py::test_parsed_question_supports_recognition_metadata -v
```

Expected: FAIL with keyword/attribute errors for missing `source_page`, `bbox`, `raw_ocr_text`, `formula_latex`, `formula_images`, or `confidence_detail`.

- [ ] **Step 3: Modify `backend/models.py`**

Find class `ParsedQuestion`. After `images = db.Column(db.Text)`, add:

```python
    source_page = db.Column(db.Integer)
    bbox = db.Column(db.Text)
    raw_ocr_text = db.Column(db.Text)
    formula_latex = db.Column(db.Text)
    formula_images = db.Column(db.Text)
    confidence_detail = db.Column(db.Text)
```

- [ ] **Step 4: Create migration script**

Create `backend/migrate_import_recognition.py`:

```python
import sqlite3

DB_PATH = 'C:/bro-dev/bro.db'

COLUMNS = [
    ('source_page', 'INTEGER'),
    ('bbox', 'TEXT'),
    ('raw_ocr_text', 'TEXT'),
    ('formula_latex', 'TEXT'),
    ('formula_images', 'TEXT'),
    ('confidence_detail', 'TEXT')
]


def column_exists(cur, table, column):
    cur.execute(f'PRAGMA table_info({table})')
    return any(row[1] == column for row in cur.fetchall())


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parsed_questions'")
    if not cur.fetchone():
        print('parsed_questions table not found; app db.create_all() will create fresh schema')
        conn.close()
        return

    for name, sql_type in COLUMNS:
        if not column_exists(cur, 'parsed_questions', name):
            cur.execute(f'ALTER TABLE parsed_questions ADD COLUMN {name} {sql_type}')
            print(f'Added parsed_questions.{name}')

    conn.commit()
    conn.close()
    print('Import recognition migration done.')


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: Run test**

```powershell
pytest tests/test_import_schema.py -v
```

Expected: PASS.

- [ ] **Step 6: Run migration on dev DB**

```powershell
python migrate_import_recognition.py
```

Expected: either `Added parsed_questions...` lines plus `Import recognition migration done.` or `parsed_questions table not found...` for a fresh DB.

- [ ] **Step 7: Commit**

```powershell
git add backend/models.py backend/migrate_import_recognition.py backend/tests/test_import_schema.py
git commit -m "feat(import): add recognition metadata fields to ParsedQuestion"
```

---

## Phase 2: Canonical Import Schema and Deterministic Parsing

### Task 2: Create import schema helpers

**Files:**
- Create: `backend/services/import_schema.py`
- Test: `backend/tests/test_import_schema.py`

- [ ] **Step 1: Add failing schema test**

Append to `backend/tests/test_import_schema.py`:

```python

def test_question_candidate_to_dict_is_stable():
    from services.import_schema import QuestionCandidate, ImageAsset, FormulaAsset

    candidate = QuestionCandidate(
        index=1,
        content='求 x^2=4 的解。',
        options=[],
        answer='±2',
        explanation='平方根定义',
        question_type='blank',
        difficulty=2,
        source_page=1,
        bbox={'x': 0, 'y': 0, 'w': 100, 'h': 80},
        raw_ocr_text='1. 求 x^2=4 的解。',
        images=[ImageAsset(path='/tmp/q1.png', url='/static/images/q1.png', image_type='diagram')],
        formulas=[FormulaAsset(latex='x^2=4', image_url='/static/images/f1.png')],
        confidence_detail={'text': 0.9, 'layout': 0.8, 'formula': 0.7}
    )

    data = candidate.to_dict()
    assert data['content'] == '求 x^2=4 的解。'
    assert data['formula_latex'] == ['x^2=4']
    assert data['formula_images'] == ['/static/images/f1.png']
    assert data['images'][0]['type'] == 'diagram'
    assert data['confidence'] == 0.8
```

- [ ] **Step 2: Run failing test**

```powershell
pytest tests/test_import_schema.py::test_question_candidate_to_dict_is_stable -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.import_schema'`.

- [ ] **Step 3: Create schema file**

Create `backend/services/import_schema.py`:

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImageAsset:
    path: str
    url: str
    image_type: str = 'diagram'
    page: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None
    ocr_text: str = ''

    def to_dict(self):
        return {
            'path': self.path,
            'url': self.url,
            'type': self.image_type,
            'page': self.page,
            'bbox': self.bbox,
            'ocr_text': self.ocr_text
        }


@dataclass
class FormulaAsset:
    latex: str
    image_url: str = ''
    bbox: Optional[Dict[str, Any]] = None
    confidence: float = 0.0

    def to_dict(self):
        return {
            'latex': self.latex,
            'image_url': self.image_url,
            'bbox': self.bbox,
            'confidence': self.confidence
        }


@dataclass
class DocumentPage:
    page: int
    text: str
    images: List[ImageAsset] = field(default_factory=list)
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_image_url: str = ''


@dataclass
class QuestionCandidate:
    index: int
    content: str
    options: List[Any] = field(default_factory=list)
    answer: str = ''
    explanation: str = ''
    question_type: str = 'unknown'
    difficulty: int = 3
    source_page: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None
    raw_ocr_text: str = ''
    images: List[ImageAsset] = field(default_factory=list)
    formulas: List[FormulaAsset] = field(default_factory=list)
    confidence_detail: Dict[str, float] = field(default_factory=dict)

    def confidence(self):
        if not self.confidence_detail:
            return 0.0
        return round(sum(self.confidence_detail.values()) / len(self.confidence_detail), 3)

    def to_dict(self):
        return {
            'index': self.index,
            'content': self.content,
            'options': self.options,
            'answer': self.answer,
            'explanation': self.explanation,
            'type': self.question_type,
            'difficulty': self.difficulty,
            'source_page': self.source_page,
            'bbox': self.bbox,
            'raw_ocr_text': self.raw_ocr_text,
            'images': [img.to_dict() for img in self.images],
            'formula_latex': [f.latex for f in self.formulas if f.latex],
            'formula_images': [f.image_url for f in self.formulas if f.image_url],
            'formula_detail': [f.to_dict() for f in self.formulas],
            'confidence_detail': self.confidence_detail,
            'confidence': self.confidence()
        }
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_import_schema.py -v
```

Expected: all tests in file PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/import_schema.py backend/tests/test_import_schema.py
git commit -m "feat(import): add canonical import schema dataclasses"
```

---

### Task 3: Create deterministic question segmenter

**Files:**
- Create: `backend/services/question_segmenter.py`
- Create: `backend/tests/test_question_segmenter.py`

- [ ] **Step 1: Write failing segmenter tests**

Create `backend/tests/test_question_segmenter.py`:

```python
from services.import_schema import DocumentPage
from services.question_segmenter import QuestionSegmenter


def test_segment_numbered_choice_questions():
    text = '''
1. 集合 A={1,2,3}, B={2,3,4}，则 A∩B=？
A. {1}
B. {2,3}
C. {4}
D. {1,2,3,4}
答案：B
解析：交集取公共元素。

2. 函数 f(x)=2x+1，则 f(3)=？
A. 5
B. 6
C. 7
D. 8
答案：C
解析：2×3+1=7。
'''
    pages = [DocumentPage(page=1, text=text)]
    candidates = QuestionSegmenter().segment(pages)
    assert len(candidates) == 2
    assert candidates[0].content.startswith('集合 A=')
    assert candidates[0].answer == 'B'
    assert len(candidates[0].options) == 4
    assert candidates[1].answer == 'C'


def test_segment_blank_question():
    text = '1. 等差数列 a1=1, d=2，则 a10=___\n答案：19\n解析：公式代入。'
    pages = [DocumentPage(page=1, text=text)]
    candidates = QuestionSegmenter().segment(pages)
    assert len(candidates) == 1
    assert candidates[0].question_type == 'blank'
    assert candidates[0].answer == '19'


def test_segment_keeps_source_page():
    text = '1. 速度单位是？\nA. m/s\nB. kg\n答案：A'
    pages = [DocumentPage(page=3, text=text)]
    candidates = QuestionSegmenter().segment(pages)
    assert candidates[0].source_page == 3
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_question_segmenter.py -v
```

Expected: FAIL because `question_segmenter.py` does not exist.

- [ ] **Step 3: Implement segmenter**

Create `backend/services/question_segmenter.py`:

```python
import re
from services.import_schema import QuestionCandidate


QUESTION_SPLIT_RE = re.compile(r'(?:^|\n)\s*(\d+)[\.、．]\s*')
OPTION_RE = re.compile(r'^\s*([A-D])\s*[\.、．]\s*(.+)$', re.MULTILINE)
ANSWER_RE = re.compile(r'(?:答案|Answer)\s*[:：]\s*([^\n]+)')
EXPLANATION_RE = re.compile(r'(?:解析|Explanation)\s*[:：]\s*([\s\S]+)$')


class QuestionSegmenter:
    def segment(self, pages):
        candidates = []
        index = 1
        for page in pages:
            parts = self._split_page(page.text)
            for raw in parts:
                candidate = self._parse_raw_question(raw, index=index, source_page=page.page)
                if candidate and candidate.content.strip():
                    candidates.append(candidate)
                    index += 1
        return candidates

    def _split_page(self, text):
        matches = list(QUESTION_SPLIT_RE.finditer(text))
        if not matches:
            stripped = text.strip()
            return [stripped] if stripped else []

        parts = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            parts.append(text[start:end].strip())
        return [p for p in parts if p]

    def _parse_raw_question(self, raw, index, source_page):
        answer = ''
        explanation = ''

        answer_match = ANSWER_RE.search(raw)
        if answer_match:
            answer = answer_match.group(1).strip()

        explanation_match = EXPLANATION_RE.search(raw)
        if explanation_match:
            explanation = explanation_match.group(1).strip()

        options = []
        for key, text in OPTION_RE.findall(raw):
            options.append({'key': key, 'text': text.strip()})

        content = raw
        content = ANSWER_RE.sub('', content)
        content = EXPLANATION_RE.sub('', content)
        content = OPTION_RE.sub('', content).strip()

        question_type = 'choice' if options else ('blank' if '___' in content or '____' in content else 'unknown')

        return QuestionCandidate(
            index=index,
            content=content,
            options=options,
            answer=answer,
            explanation=explanation,
            question_type=question_type,
            difficulty=3,
            source_page=source_page,
            raw_ocr_text=raw,
            confidence_detail={'layout': 0.85, 'text': 0.9}
        )
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_question_segmenter.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/question_segmenter.py backend/tests/test_question_segmenter.py
git commit -m "feat(import): add deterministic question segmenter"
```

---

## Phase 3: Document Ingestion and Recognition Pipeline

### Task 4: Create DocumentIngestor

**Files:**
- Create: `backend/services/document_ingestor.py`
- Create: `backend/tests/test_document_ingestor.py`

- [ ] **Step 1: Write failing ingestion tests**

Create `backend/tests/test_document_ingestor.py`:

```python
from services.document_ingestor import DocumentIngestor


def test_ingest_txt_file(tmp_path):
    p = tmp_path / 'questions.txt'
    p.write_text('1. 1+1=?\n答案：2', encoding='utf-8')
    pages = DocumentIngestor().ingest(str(p), 'txt')
    assert len(pages) == 1
    assert pages[0].page == 1
    assert '1+1' in pages[0].text


def test_ingest_image_file_creates_page(tmp_path):
    from PIL import Image
    img = Image.new('RGB', (100, 80), color='white')
    p = tmp_path / 'q.png'
    img.save(p)
    pages = DocumentIngestor().ingest(str(p), 'png')
    assert len(pages) == 1
    assert pages[0].page == 1
    assert len(pages[0].images) == 1
    assert pages[0].images[0].image_type == 'source_image'
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_document_ingestor.py -v
```

Expected: FAIL because `document_ingestor.py` does not exist.

- [ ] **Step 3: Implement ingestor**

Create `backend/services/document_ingestor.py`:

```python
import os
from PIL import Image
from services.import_schema import DocumentPage, ImageAsset
from services.file_processor import FileProcessor


class DocumentIngestor:
    def __init__(self):
        self.processor = FileProcessor()

    def ingest(self, file_path, file_type):
        file_type = file_type.lower()
        if file_type == 'txt':
            return self._ingest_txt(file_path)
        if file_type in ('png', 'jpg', 'jpeg'):
            return self._ingest_image(file_path)
        if file_type in ('pdf', 'doc', 'docx'):
            return self._ingest_via_file_processor(file_path, file_type)
        raise ValueError(f'Unsupported file type: {file_type}')

    def _ingest_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return [DocumentPage(page=1, text=text, images=[], blocks=[])]

    def _ingest_image(self, file_path):
        filename = os.path.basename(file_path)
        image = Image.open(file_path)
        image.verify()
        asset = ImageAsset(
            path=file_path,
            url=f'/uploads/{filename}',
            image_type='source_image',
            page=1
        )
        return [DocumentPage(page=1, text='', images=[asset], blocks=[], page_image_url=asset.url)]

    def _ingest_via_file_processor(self, file_path, file_type):
        result = self.processor.process_file(file_path, file_type)
        images_by_page = {}
        for img in result.get('images', []):
            page = img.get('page', 1)
            images_by_page.setdefault(page, []).append(ImageAsset(
                path=img.get('path', ''),
                url=img.get('url', ''),
                image_type='embedded',
                page=page
            ))

        pages = []
        for item in result.get('text_content', []):
            page_no = item.get('page', 1)
            pages.append(DocumentPage(
                page=page_no,
                text=item.get('text', ''),
                images=images_by_page.get(page_no, []),
                blocks=[]
            ))
        return pages
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_document_ingestor.py -v
```

Expected: 2 PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/document_ingestor.py backend/tests/test_document_ingestor.py
git commit -m "feat(import): add document ingestor for txt/image/pdf/word"
```

---

### Task 5: Create recognition pipeline and AI JSON parser

**Files:**
- Create: `backend/services/ai_json.py`
- Create: `backend/services/recognition_pipeline.py`
- Create: `backend/tests/test_recognition_pipeline.py`

- [ ] **Step 1: Write tests**

Create `backend/tests/test_recognition_pipeline.py`:

```python
from services.import_schema import DocumentPage
from services.recognition_pipeline import RecognitionPipeline
from services.ai_json import parse_ai_questions_json


def test_parse_ai_questions_json_strips_markdown_fence():
    text = '```json\n[{"content":"1+1=?","answer":"2","type":"blank","difficulty":1}]\n```'
    questions = parse_ai_questions_json(text)
    assert len(questions) == 1
    assert questions[0]['answer'] == '2'


def test_pipeline_segments_text_without_ai():
    pages = [DocumentPage(page=1, text='1. 1+1=?\n答案：2')]
    candidates = RecognitionPipeline().recognize(pages, subject='数学')
    assert len(candidates) == 1
    assert candidates[0].answer == '2'


def test_pipeline_marks_image_only_as_low_confidence_candidate(tmp_path):
    from services.import_schema import ImageAsset
    pages = [DocumentPage(page=1, text='', images=[ImageAsset(path='x.png', url='/x.png', image_type='source_image')])]
    candidates = RecognitionPipeline().recognize(pages, subject='数学')
    assert len(candidates) == 1
    assert candidates[0].confidence_detail['text'] < 0.5
    assert candidates[0].images[0].url == '/x.png'
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_recognition_pipeline.py -v
```

Expected: FAIL for missing modules.

- [ ] **Step 3: Implement AI JSON helper**

Create `backend/services/ai_json.py`:

```python
import json
import re


def parse_ai_questions_json(text):
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json)?', '', cleaned).strip()
    cleaned = re.sub(r'```$', '', cleaned).strip()

    match = re.search(r'\[[\s\S]*\]', cleaned)
    if match:
        cleaned = match.group(0)

    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError('AI output must be a list')

    normalized = []
    for item in data:
        if not isinstance(item, dict):
            continue
        normalized.append({
            'content': item.get('content', ''),
            'options': item.get('options', []),
            'answer': item.get('answer', ''),
            'explanation': item.get('explanation', ''),
            'type': item.get('type', 'unknown'),
            'difficulty': item.get('difficulty', 3)
        })
    return normalized
```

- [ ] **Step 4: Implement recognition pipeline**

Create `backend/services/recognition_pipeline.py`:

```python
from services.import_schema import QuestionCandidate
from services.question_segmenter import QuestionSegmenter


class RecognitionPipeline:
    def __init__(self):
        self.segmenter = QuestionSegmenter()

    def recognize(self, pages, subject=''):
        text_pages = [p for p in pages if p.text and p.text.strip()]
        candidates = []

        if text_pages:
            candidates.extend(self.segmenter.segment(text_pages))

        image_only_pages = [p for p in pages if not (p.text and p.text.strip()) and p.images]
        for page in image_only_pages:
            candidates.append(QuestionCandidate(
                index=len(candidates) + 1,
                content='[图片题待识别]',
                options=[],
                answer='',
                explanation='',
                question_type='unknown',
                difficulty=3,
                source_page=page.page,
                raw_ocr_text='',
                images=page.images,
                confidence_detail={'text': 0.2, 'layout': 0.4, 'image': 0.8}
            ))

        return candidates
```

- [ ] **Step 5: Run tests**

```powershell
pytest tests/test_recognition_pipeline.py -v
```

Expected: 3 PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend/services/ai_json.py backend/services/recognition_pipeline.py backend/tests/test_recognition_pipeline.py
git commit -m "feat(import): add recognition pipeline and AI JSON parser"
```

---

### Task 6: Create question normalizer

**Files:**
- Create: `backend/services/question_normalizer.py`
- Test: `backend/tests/test_recognition_pipeline.py`

- [ ] **Step 1: Add test**

Append to `backend/tests/test_recognition_pipeline.py`:

```python

def test_normalizer_prepares_parsed_question_payload():
    from services.import_schema import QuestionCandidate, FormulaAsset
    from services.question_normalizer import QuestionNormalizer

    candidate = QuestionCandidate(
        index=1,
        content='求 x^2=4',
        answer='±2',
        question_type='blank',
        formulas=[FormulaAsset(latex='x^2=4', image_url='/static/f.png')],
        confidence_detail={'text': 0.9, 'formula': 0.8}
    )
    payload = QuestionNormalizer().to_parsed_payload(candidate, defaults={
        'exam_type': 'gaokao',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '方程'
    })

    assert payload['content'] == '求 x^2=4'
    assert payload['subject'] == '数学'
    assert payload['formula_latex'] == ['x^2=4']
    assert payload['confidence'] == 0.85
```

- [ ] **Step 2: Run failing test**

```powershell
pytest tests/test_recognition_pipeline.py::test_normalizer_prepares_parsed_question_payload -v
```

Expected: FAIL for missing `question_normalizer.py`.

- [ ] **Step 3: Implement normalizer**

Create `backend/services/question_normalizer.py`:

```python
class QuestionNormalizer:
    def to_parsed_payload(self, candidate, defaults):
        data = candidate.to_dict()
        return {
            'content': data['content'],
            'options': data['options'],
            'answer': data['answer'],
            'explanation': data['explanation'],
            'type': data['type'],
            'difficulty': data['difficulty'],
            'exam_type': defaults.get('exam_type', ''),
            'subject': defaults.get('subject', ''),
            'grade': defaults.get('grade', ''),
            'knowledge_point': defaults.get('knowledge_point', '不详'),
            'source_page': data['source_page'],
            'bbox': data['bbox'],
            'images': data['images'],
            'formula_latex': data['formula_latex'],
            'formula_images': data['formula_images'],
            'raw_ocr_text': data['raw_ocr_text'],
            'confidence_detail': data['confidence_detail'],
            'confidence': data['confidence']
        }
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_recognition_pipeline.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/question_normalizer.py backend/tests/test_recognition_pipeline.py
git commit -m "feat(import): add question normalizer for ParsedQuestion payloads"
```

---

## Phase 4: Import APIs

### Task 7: Add single and batch import APIs

**Files:**
- Modify: `backend/routes/import.py`
- Create: `backend/tests/test_import_api_single_batch.py`

- [ ] **Step 1: Write API tests**

Create `backend/tests/test_import_api_single_batch.py`:

```python
import io


def test_single_text_import_creates_one_parsed_question(client):
    resp = client.post('/api/import/single', json={
        'text': '1. 1+1=?\n答案：2',
        'exam_type': 'gaokao',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '计算'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['total_questions'] == 1
    assert data['questions'][0]['answer'] == '2'


def test_single_import_requires_subject(client):
    resp = client.post('/api/import/single', json={'text': '1. hi'})
    assert resp.status_code == 400


def test_batch_txt_import_creates_batch_and_questions(client):
    sample = '1. 1+1=?\n答案：2\n\n2. 2+2=?\n答案：4'
    data = {
        'file': (io.BytesIO(sample.encode('utf-8')), 'questions.txt'),
        'exam_type': 'gaokao',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '计算'
    }
    resp = client.post('/api/import/batch', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['total_questions'] == 2
    assert body['batch_id']
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_import_api_single_batch.py -v
```

Expected: FAIL because endpoints do not exist.

- [ ] **Step 3: Modify import route imports**

At top of `backend/routes/import.py`, ensure these imports exist:

```python
from services.document_ingestor import DocumentIngestor
from services.recognition_pipeline import RecognitionPipeline
from services.question_normalizer import QuestionNormalizer
```

- [ ] **Step 4: Append helper functions to `backend/routes/import.py`**

Append before route definitions or near top after `allowed_file`:

```python
def _parsed_from_payload(batch_id, payload):
    return ParsedQuestion(
        batch_id=batch_id,
        raw_content=json.dumps(payload, ensure_ascii=False),
        content=payload.get('content', ''),
        options=json.dumps(payload.get('options', []), ensure_ascii=False),
        answer=payload.get('answer', ''),
        explanation=payload.get('explanation', ''),
        exam_type=payload.get('exam_type', ''),
        subject=payload.get('subject', ''),
        grade=payload.get('grade', ''),
        knowledge_point=payload.get('knowledge_point', '不详'),
        type=payload.get('type', 'unknown'),
        difficulty=payload.get('difficulty', 3),
        confidence=payload.get('confidence', 0),
        status='pending',
        source_page=payload.get('source_page'),
        bbox=json.dumps(payload.get('bbox'), ensure_ascii=False),
        images=json.dumps(payload.get('images', []), ensure_ascii=False),
        formula_latex=json.dumps(payload.get('formula_latex', []), ensure_ascii=False),
        formula_images=json.dumps(payload.get('formula_images', []), ensure_ascii=False),
        raw_ocr_text=payload.get('raw_ocr_text', ''),
        confidence_detail=json.dumps(payload.get('confidence_detail', {}), ensure_ascii=False)
    )


def _serialize_parsed_question(q):
    return {
        'id': q.id,
        'content': q.content,
        'options': json.loads(q.options) if q.options else [],
        'answer': q.answer,
        'explanation': q.explanation,
        'exam_type': q.exam_type,
        'subject': q.subject,
        'grade': q.grade,
        'knowledge_point': q.knowledge_point,
        'type': q.type,
        'difficulty': q.difficulty,
        'confidence': q.confidence,
        'status': q.status,
        'source_page': q.source_page,
        'bbox': json.loads(q.bbox) if q.bbox else None,
        'images': json.loads(q.images) if q.images else [],
        'formula_latex': json.loads(q.formula_latex) if q.formula_latex else [],
        'formula_images': json.loads(q.formula_images) if q.formula_images else [],
        'raw_ocr_text': q.raw_ocr_text,
        'confidence_detail': json.loads(q.confidence_detail) if q.confidence_detail else {}
    }
```

- [ ] **Step 5: Add `/single` route**

Append to `backend/routes/import.py`:

```python
@import_bp.route('/single', methods=['POST'])
def import_single():
    data = request.get_json() or {}
    text = data.get('text', '')
    exam_type = data.get('exam_type', '')
    subject = data.get('subject', '')
    grade = data.get('grade', '')
    knowledge_point = data.get('knowledge_point', '不详')

    if not exam_type:
        return jsonify({'error': '请选择考试体系'}), 400
    if not subject:
        return jsonify({'error': '请选择科目'}), 400
    if not text.strip():
        return jsonify({'error': '请输入题目内容'}), 400

    from services.import_schema import DocumentPage
    pages = [DocumentPage(page=1, text=text)]
    candidates = RecognitionPipeline().recognize(pages, subject=subject)
    normalizer = QuestionNormalizer()

    batch = ImportBatch(
        source_type='single',
        source_file='single-input',
        source_url='',
        status='reviewing',
        exam_type=exam_type,
        subject=subject,
        grade=grade,
        knowledge_point=knowledge_point,
        created_by=data.get('created_by', 'admin'),
        parsed_questions=len(candidates)
    )
    db.session.add(batch)
    db.session.commit()

    parsed_items = []
    defaults = {'exam_type': exam_type, 'subject': subject, 'grade': grade, 'knowledge_point': knowledge_point}
    for candidate in candidates:
        payload = normalizer.to_parsed_payload(candidate, defaults)
        parsed = _parsed_from_payload(batch.id, payload)
        db.session.add(parsed)
        parsed_items.append(parsed)

    db.session.commit()

    return jsonify({
        'success': True,
        'batch_id': batch.id,
        'total_questions': len(parsed_items),
        'questions': [_serialize_parsed_question(q) for q in parsed_items]
    })
```

- [ ] **Step 6: Add `/batch` route**

Append to `backend/routes/import.py`:

```python
@import_bp.route('/batch', methods=['POST'])
def import_batch():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400

    exam_type = request.form.get('exam_type', '')
    subject = request.form.get('subject', '')
    grade = request.form.get('grade', '')
    knowledge_point = request.form.get('knowledge_point', '不详')
    if not exam_type:
        return jsonify({'error': '请选择考试体系'}), 400
    if not subject:
        return jsonify({'error': '请选择科目'}), 400

    processor = FileProcessor()
    filename = secure_filename(file.filename)
    file_path = processor.save_upload(file, filename)
    file_type = filename.rsplit('.', 1)[1].lower()

    batch = ImportBatch(
        source_type=file_type,
        source_file=filename,
        source_url=file_path,
        status='processing',
        exam_type=exam_type,
        subject=subject,
        grade=grade,
        knowledge_point=knowledge_point,
        created_by=request.form.get('created_by', 'admin')
    )
    db.session.add(batch)
    db.session.commit()

    try:
        pages = DocumentIngestor().ingest(file_path, file_type)
        candidates = RecognitionPipeline().recognize(pages, subject=subject)
        normalizer = QuestionNormalizer()
        defaults = {'exam_type': exam_type, 'subject': subject, 'grade': grade, 'knowledge_point': knowledge_point}
        parsed_items = []
        for candidate in candidates:
            payload = normalizer.to_parsed_payload(candidate, defaults)
            parsed = _parsed_from_payload(batch.id, payload)
            db.session.add(parsed)
            parsed_items.append(parsed)

        batch.status = 'reviewing'
        batch.parsed_questions = len(parsed_items)
        db.session.commit()

        return jsonify({
            'success': True,
            'batch_id': batch.id,
            'status': batch.status,
            'total_questions': len(parsed_items)
        })
    except Exception as exc:
        batch.status = 'failed'
        db.session.commit()
        return jsonify({'error': str(exc), 'batch_id': batch.id}), 500
```

- [ ] **Step 7: Run tests**

```powershell
pytest tests/test_import_api_single_batch.py -v
```

Expected: 3 PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/routes/import.py backend/tests/test_import_api_single_batch.py
git commit -m "feat(import): add single and batch import APIs"
```

---

### Task 8: Add parsed-question edit, split, merge, and safe-approve APIs

**Files:**
- Modify: `backend/routes/import.py`
- Create: `backend/tests/test_import_review_actions.py`

- [ ] **Step 1: Write review action tests**

Create `backend/tests/test_import_review_actions.py`:

```python
import json


def _create_parsed(app):
    from models import db, ImportBatch, ParsedQuestion
    with app.app_context():
        batch = ImportBatch(source_type='txt', source_file='x.txt', source_url='', status='reviewing')
        db.session.add(batch)
        db.session.commit()
        pq = ParsedQuestion(
            batch_id=batch.id,
            raw_content='{}',
            content='1+1=?',
            options=json.dumps([]),
            answer='2',
            explanation='',
            exam_type='gaokao',
            subject='数学',
            grade='高一',
            knowledge_point='计算',
            type='blank',
            difficulty=1,
            confidence=0.9,
            status='pending'
        )
        db.session.add(pq)
        db.session.commit()
        return batch.id, pq.id


def test_update_parsed_question(client, app):
    _, pid = _create_parsed(app)
    resp = client.put(f'/api/import/parsed/{pid}', json={'content': '2+2=?', 'answer': '4'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['question']['content'] == '2+2=?'
    assert body['question']['answer'] == '4'


def test_split_parsed_question(client, app):
    _, pid = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid}/split', json={
        'first': {'content': '1+1=?', 'answer': '2'},
        'second': {'content': '2+2=?', 'answer': '4'}
    })
    assert resp.status_code == 200
    assert resp.get_json()['created_id']


def test_merge_parsed_questions(client, app):
    batch_id, pid1 = _create_parsed(app)
    _, pid2 = _create_parsed(app)
    resp = client.post(f'/api/import/parsed/{pid2}/merge', json={'target_id': pid1})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_approve_safe_approves_high_confidence(client, app):
    batch_id, pid = _create_parsed(app)
    resp = client.post(f'/api/import/batch/{batch_id}/approve-safe', json={'min_confidence': 0.8})
    assert resp.status_code == 200
    assert resp.get_json()['approved_count'] == 1
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_import_review_actions.py -v
```

Expected: FAIL because endpoints do not exist.

- [ ] **Step 3: Append routes to `backend/routes/import.py`**

Append:

```python
@import_bp.route('/parsed/<int:question_id>', methods=['PUT'])
def update_parsed_question(question_id):
    data = request.get_json() or {}
    parsed = db.session.get(ParsedQuestion, question_id)
    if not parsed:
        return jsonify({'error': 'not_found'}), 404

    for field in ['content', 'answer', 'explanation', 'subject', 'grade', 'knowledge_point', 'type', 'difficulty']:
        if field in data:
            setattr(parsed, field, data[field])
    if 'options' in data:
        parsed.options = json.dumps(data.get('options', []), ensure_ascii=False)
    if 'images' in data:
        parsed.images = json.dumps(data.get('images', []), ensure_ascii=False)
    if 'formula_latex' in data:
        parsed.formula_latex = json.dumps(data.get('formula_latex', []), ensure_ascii=False)
    if 'formula_images' in data:
        parsed.formula_images = json.dumps(data.get('formula_images', []), ensure_ascii=False)

    db.session.commit()
    return jsonify({'success': True, 'question': _serialize_parsed_question(parsed)})


@import_bp.route('/parsed/<int:question_id>/split', methods=['POST'])
def split_parsed_question(question_id):
    data = request.get_json() or {}
    parsed = db.session.get(ParsedQuestion, question_id)
    if not parsed:
        return jsonify({'error': 'not_found'}), 404

    first = data.get('first', {})
    second = data.get('second', {})
    parsed.content = first.get('content', parsed.content)
    parsed.answer = first.get('answer', parsed.answer)
    parsed.explanation = first.get('explanation', parsed.explanation)

    created = ParsedQuestion(
        batch_id=parsed.batch_id,
        raw_content=json.dumps(second, ensure_ascii=False),
        content=second.get('content', ''),
        options=json.dumps(second.get('options', []), ensure_ascii=False),
        answer=second.get('answer', ''),
        explanation=second.get('explanation', ''),
        exam_type=parsed.exam_type,
        subject=parsed.subject,
        grade=parsed.grade,
        knowledge_point=parsed.knowledge_point,
        type=second.get('type', parsed.type),
        difficulty=second.get('difficulty', parsed.difficulty),
        confidence=parsed.confidence,
        status='pending',
        source_page=parsed.source_page
    )
    db.session.add(created)
    db.session.commit()
    return jsonify({'success': True, 'created_id': created.id, 'updated_id': parsed.id})


@import_bp.route('/parsed/<int:question_id>/merge', methods=['POST'])
def merge_parsed_question(question_id):
    data = request.get_json() or {}
    target_id = data.get('target_id')
    source = db.session.get(ParsedQuestion, question_id)
    target = db.session.get(ParsedQuestion, target_id)
    if not source or not target:
        return jsonify({'error': 'not_found'}), 404

    target.content = (target.content or '') + '\n' + (source.content or '')
    if source.explanation:
        target.explanation = ((target.explanation or '') + '\n' + source.explanation).strip()
    source.status = 'rejected'
    source.review_notes = f'Merged into ParsedQuestion #{target.id}'
    db.session.commit()
    return jsonify({'success': True, 'target_id': target.id, 'merged_id': source.id})


@import_bp.route('/batch/<int:batch_id>/approve-safe', methods=['POST'])
def approve_safe_questions(batch_id):
    data = request.get_json() or {}
    min_confidence = float(data.get('min_confidence', 0.85))
    questions = ParsedQuestion.query.filter_by(batch_id=batch_id, status='pending').all()
    approved_count = 0
    for parsed in questions:
        if (parsed.confidence or 0) < min_confidence:
            continue
        question = Question(
            region=data.get('region', 'mainland'),
            subject=parsed.subject,
            grade=parsed.grade,
            knowledge_point=parsed.knowledge_point,
            type=parsed.type,
            difficulty=parsed.difficulty,
            content=parsed.content,
            answer=parsed.answer,
            explanation=parsed.explanation,
            options=parsed.options,
            source='import',
            status='approved'
        )
        db.session.add(question)
        parsed.status = 'approved'
        approved_count += 1

    batch = db.session.get(ImportBatch, batch_id)
    if batch:
        batch.approved_questions = (batch.approved_questions or 0) + approved_count
        if approved_count:
            batch.status = 'completed'

    db.session.commit()
    return jsonify({'success': True, 'approved_count': approved_count})
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_import_review_actions.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/routes/import.py backend/tests/test_import_review_actions.py
git commit -m "feat(import): add parsed edit split merge and safe batch approve APIs"
```

---

## Phase 5: Web Admin

### Task 9: Extend web-admin API service

**Files:**
- Modify: `web-admin/src/services/api.js`

- [ ] **Step 1: Replace API service file**

Replace `web-admin/src/services/api.js` with:

```javascript
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const uploadFile = (file, examType, subject, grade, knowledgePoint) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('exam_type', examType);
  formData.append('subject', subject);
  formData.append('grade', grade);
  formData.append('knowledge_point', knowledgePoint);
  formData.append('created_by', 'admin');
  return api.post('/import/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const importSingleQuestion = (data) => api.post('/import/single', data);

export const getBatches = (page = 1) => api.get('/import/batches', { params: { page } });
export const getBatchDetail = (batchId) => api.get(`/import/batch/${batchId}`);
export const getBatchQuestions = (batchId, status = 'pending') => api.get(`/import/batch/${batchId}/questions`, { params: { status } });

export const updateParsedQuestion = (questionId, data) => api.put(`/import/parsed/${questionId}`, data);
export const approveQuestion = (questionId, data) => api.post(`/import/question/${questionId}/approve`, data);
export const rejectQuestion = (questionId, data) => api.post(`/import/question/${questionId}/reject`, data);
export const splitParsedQuestion = (questionId, data) => api.post(`/import/parsed/${questionId}/split`, data);
export const mergeParsedQuestion = (questionId, targetId) => api.post(`/import/parsed/${questionId}/merge`, { target_id: targetId });
export const approveSafeQuestions = (batchId, minConfidence = 0.85) => api.post(`/import/batch/${batchId}/approve-safe`, { min_confidence: minConfidence });

export default api;
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/services/api.js
git commit -m "feat(admin): add import recognition API client methods"
```

---

### Task 10: Update Import page for single/batch modes

**Files:**
- Modify: `web-admin/src/pages/Import/Import.js`
- Modify: `web-admin/src/pages/Import/Import.css`

- [ ] **Step 1: Replace `Import.js`**

Replace `web-admin/src/pages/Import/Import.js` with:

```javascript
import React, { useState, useEffect } from 'react';
import { Upload, message, Card, List, Tag, Button, Select, Tabs, Form, Input } from 'antd';
import { InboxOutlined, FilePdfOutlined, FileWordOutlined, FileImageOutlined, FileTextOutlined } from '@ant-design/icons';
import { uploadFile, getBatches, importSingleQuestion } from '../../services/api';
import './Import.css';

const { Dragger } = Upload;
const { Option } = Select;
const { TextArea } = Input;

const examOptions = [
  { value: 'gaokao', label: '高考' },
  { value: 'dse', label: '香港 DSE' }
];
const subjectOptions = ['数学', '物理', '化学', '生物'];
const gradeOptions = ['高一', '高二', '高三', '中四', '中五', '中六'];

const ImportPage = () => {
  const [batches, setBatches] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();
  const [singleForm] = Form.useForm();

  useEffect(() => { loadBatches(); }, []);

  const loadBatches = async () => {
    const res = await getBatches();
    setBatches(res.data.batches || []);
  };

  const handleBatchUpload = async ({ file }) => {
    const values = form.getFieldsValue();
    if (!values.examType || !values.subject) {
      message.error('请选择考试体系和科目');
      return;
    }
    setUploading(true);
    try {
      const res = await uploadFile(file, values.examType, values.subject, values.grade || '', values.knowledgePoint || '不详');
      message.success(`解析完成：${res.data.total_questions} 道题等待审核`);
      loadBatches();
    } catch (e) {
      message.error(e.response?.data?.error || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleSingleSubmit = async (values) => {
    try {
      const res = await importSingleQuestion({
        text: values.text,
        exam_type: values.examType,
        subject: values.subject,
        grade: values.grade || '',
        knowledge_point: values.knowledgePoint || '不详',
        created_by: 'admin'
      });
      message.success(`单题解析成功：${res.data.total_questions} 道题等待审核`);
      singleForm.resetFields(['text']);
      loadBatches();
    } catch (e) {
      message.error(e.response?.data?.error || '单题导入失败');
    }
  };

  const getFileIcon = (type) => {
    if (type === 'pdf') return <FilePdfOutlined />;
    if (type === 'doc' || type === 'docx') return <FileWordOutlined />;
    if (['png', 'jpg', 'jpeg'].includes(type)) return <FileImageOutlined />;
    return <FileTextOutlined />;
  };

  const renderMetaForm = (targetForm) => (
    <Form form={targetForm} layout="inline" className="meta-form">
      <Form.Item name="examType" label="考试体系" rules={[{ required: true }]}>
        <Select style={{ width: 140 }} placeholder="考试体系">
          {examOptions.map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="subject" label="科目" rules={[{ required: true }]}>
        <Select style={{ width: 120 }} placeholder="科目">
          {subjectOptions.map(s => <Option key={s} value={s}>{s}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="grade" label="年级">
        <Select style={{ width: 120 }} placeholder="年级">
          {gradeOptions.map(g => <Option key={g} value={g}>{g}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="knowledgePoint" label="知识点">
        <Input style={{ width: 160 }} placeholder="可选" />
      </Form.Item>
    </Form>
  );

  return (
    <div className="import-page">
      <Tabs defaultActiveKey="batch" items={[
        {
          key: 'batch',
          label: '试卷批量导入',
          children: (
            <Card title="上传试卷文件" className="upload-card">
              {renderMetaForm(form)}
              <Dragger customRequest={handleBatchUpload} showUploadList={false} disabled={uploading} accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.txt">
                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">支持 PDF、Word、图片、TXT；上传后进入待审核队列</p>
              </Dragger>
            </Card>
          )
        },
        {
          key: 'single',
          label: '单题导入',
          children: (
            <Card title="粘贴单题文本" className="upload-card">
              {renderMetaForm(singleForm)}
              <Form form={singleForm} layout="vertical" onFinish={handleSingleSubmit} className="single-form">
                <Form.Item name="text" label="题目内容" rules={[{ required: true, message: '请输入题目内容' }]}>
                  <TextArea rows={8} placeholder="例：1. 已知 x²=4，求 x。\n答案：±2\n解析：平方根定义。" />
                </Form.Item>
                <Button type="primary" htmlType="submit">解析单题</Button>
              </Form>
            </Card>
          )
        }
      ]} />

      <Card title="导入历史" className="history-card">
        <List
          dataSource={batches}
          renderItem={batch => (
            <List.Item>
              <List.Item.Meta
                avatar={getFileIcon(batch.source_type)}
                title={`${batch.source_file} (${batch.parsed_questions || 0} 题)`}
                description={`${batch.subject || '-'} / ${batch.grade || '-'} / ${batch.created_at}`}
              />
              <Tag color={batch.status === 'reviewing' ? 'orange' : batch.status === 'completed' ? 'green' : 'blue'}>{batch.status}</Tag>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default ImportPage;
```

- [ ] **Step 2: Replace `Import.css`**

Replace `web-admin/src/pages/Import/Import.css` with:

```css
.import-page { padding: 24px; }
.upload-card { margin-bottom: 24px; }
.history-card { margin-top: 24px; }
.meta-form { margin-bottom: 20px; row-gap: 12px; }
.single-form { margin-top: 20px; }
.ant-upload-drag-icon { color: #4A90D9; }
```

- [ ] **Step 3: Commit**

```powershell
git add web-admin/src/pages/Import/Import.js web-admin/src/pages/Import/Import.css
git commit -m "feat(admin): support single and batch question import UI"
```

---

### Task 11: Replace Review page with three-column workspace

**Files:**
- Modify: `web-admin/src/pages/Review/Review.js`
- Modify: `web-admin/src/pages/Review/Review.css`

- [ ] **Step 1: Replace Review.js**

Replace `web-admin/src/pages/Review/Review.js` with:

```javascript
import React, { useEffect, useState } from 'react';
import { Button, Card, Form, Input, List, Select, Space, Tag, message, Modal } from 'antd';
import { CheckOutlined, CloseOutlined, SaveOutlined, SplitCellsOutlined, MergeCellsOutlined } from '@ant-design/icons';
import { getBatches, getBatchQuestions, updateParsedQuestion, approveQuestion, rejectQuestion, splitParsedQuestion, mergeParsedQuestion, approveSafeQuestions } from '../../services/api';
import './Review.css';

const { TextArea } = Input;
const { Option } = Select;

const ReviewPage = () => {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [current, setCurrent] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => { loadBatches(); }, []);

  const loadBatches = async () => {
    const res = await getBatches();
    setBatches((res.data.batches || []).filter(b => ['reviewing', 'processing', 'failed'].includes(b.status)));
  };

  const loadQuestions = async (batchId) => {
    setSelectedBatch(batchId);
    const res = await getBatchQuestions(batchId, 'pending');
    setQuestions(res.data.questions || []);
    setCurrent(null);
  };

  const selectQuestion = (q) => {
    setCurrent(q);
    form.setFieldsValue({
      content: q.content,
      options: (q.options || []).map(o => typeof o === 'string' ? o : `${o.key || ''}. ${o.text || ''}`).join('\n'),
      answer: q.answer,
      explanation: q.explanation,
      type: q.type,
      difficulty: q.difficulty,
      subject: q.subject,
      grade: q.grade,
      knowledge_point: q.knowledge_point,
      formula_latex: (q.formula_latex || []).join('\n')
    });
  };

  const valuesToPayload = (values) => ({
    ...values,
    options: (values.options || '').split('\n').map(line => line.trim()).filter(Boolean),
    formula_latex: (values.formula_latex || '').split('\n').map(line => line.trim()).filter(Boolean)
  });

  const saveDraft = async () => {
    if (!current) return;
    const values = await form.validateFields();
    const res = await updateParsedQuestion(current.id, valuesToPayload(values));
    message.success('已保存');
    const updated = res.data.question;
    setCurrent(updated);
    setQuestions(qs => qs.map(q => q.id === updated.id ? updated : q));
  };

  const approve = async () => {
    if (!current) return;
    const values = await form.validateFields();
    await updateParsedQuestion(current.id, valuesToPayload(values));
    await approveQuestion(current.id, { ...valuesToPayload(values), region: 'mainland' });
    message.success('已通过并入库');
    loadQuestions(selectedBatch);
  };

  const reject = async () => {
    if (!current) return;
    await rejectQuestion(current.id, { notes: '管理员驳回' });
    message.success('已驳回');
    loadQuestions(selectedBatch);
  };

  const splitQuestion = async () => {
    if (!current) return;
    const values = await form.validateFields();
    Modal.confirm({
      title: '拆分题目',
      content: '将当前题复制拆分为两条待审核题，第二题内容可在生成后编辑。',
      onOk: async () => {
        await splitParsedQuestion(current.id, {
          first: valuesToPayload(values),
          second: { content: '新拆分题目', answer: '', options: [], explanation: '' }
        });
        message.success('已拆分');
        loadQuestions(selectedBatch);
      }
    });
  };

  const mergeToPrevious = async () => {
    if (!current) return;
    const idx = questions.findIndex(q => q.id === current.id);
    if (idx <= 0) { message.warning('没有上一题可合并'); return; }
    await mergeParsedQuestion(current.id, questions[idx - 1].id);
    message.success('已合并到上一题');
    loadQuestions(selectedBatch);
  };

  const approveSafe = async () => {
    if (!selectedBatch) return;
    const res = await approveSafeQuestions(selectedBatch, 0.85);
    message.success(`已批量通过 ${res.data.approved_count} 题`);
    loadQuestions(selectedBatch);
  };

  return (
    <div className="review-workspace">
      <aside className="review-left">
        <Card title="导入批次" size="small">
          <List
            dataSource={batches}
            renderItem={b => (
              <List.Item className={selectedBatch === b.id ? 'selected-batch' : ''} onClick={() => loadQuestions(b.id)}>
                <List.Item.Meta title={b.source_file} description={`${b.subject || '-'} · ${b.parsed_questions || 0}题`} />
                <Tag>{b.status}</Tag>
              </List.Item>
            )}
          />
        </Card>

        {selectedBatch && <Card title={`题目列表 (${questions.length})`} size="small" className="question-list-card" extra={<Button size="small" onClick={approveSafe}>高置信批量通过</Button>}>
          <List
            dataSource={questions}
            renderItem={(q, i) => (
              <List.Item className={current?.id === q.id ? 'selected-question' : ''} onClick={() => selectQuestion(q)}>
                <div className="q-list-row">
                  <span>#{i + 1}</span>
                  <Tag color={(q.confidence || 0) >= 0.85 ? 'green' : 'orange'}>{Math.round((q.confidence || 0) * 100)}%</Tag>
                  <span className="q-list-content">{q.content}</span>
                </div>
              </List.Item>
            )}
          />
        </Card>}
      </aside>

      <main className="review-middle">
        <Card title="原文 / 原图预览">
          {!current && <div className="empty-preview">请选择一道题</div>}
          {current && <>
            <div className="preview-meta">来源页：{current.source_page || '-'}　题型：{current.type}</div>
            <div className="preview-ocr"><pre>{current.raw_ocr_text || current.content}</pre></div>
            <div className="preview-images">
              {(current.images || []).map((img, i) => <img key={i} alt="关联图" src={img.url || img} />)}
              {(current.formula_images || []).map((url, i) => <img key={`f-${i}`} alt="公式截图" src={url} />)}
            </div>
          </>}
        </Card>
      </main>

      <aside className="review-right">
        <Card title="结构化编辑器">
          {!current && <div className="empty-preview">等待选择题目</div>}
          {current && <Form form={form} layout="vertical">
            <Form.Item label="题干" name="content" rules={[{ required: true }]}><TextArea rows={5} /></Form.Item>
            <Form.Item label="选项（每行一个）" name="options"><TextArea rows={4} /></Form.Item>
            <Form.Item label="答案" name="answer"><Input /></Form.Item>
            <Form.Item label="解析" name="explanation"><TextArea rows={3} /></Form.Item>
            <Form.Item label="LaTeX 公式（每行一个）" name="formula_latex"><TextArea rows={2} /></Form.Item>
            <Space wrap>
              <Form.Item label="题型" name="type" rules={[{ required: true }]}><Select style={{ width: 120 }}><Option value="choice">选择题</Option><Option value="blank">填空题</Option><Option value="comprehensive">解答题</Option><Option value="unknown">未知</Option></Select></Form.Item>
              <Form.Item label="难度" name="difficulty"><Select style={{ width: 100 }}>{[1,2,3,4,5].map(d => <Option key={d} value={d}>{d}星</Option>)}</Select></Form.Item>
              <Form.Item label="科目" name="subject"><Input style={{ width: 120 }} /></Form.Item>
              <Form.Item label="年级" name="grade"><Input style={{ width: 120 }} /></Form.Item>
              <Form.Item label="知识点" name="knowledge_point"><Input style={{ width: 160 }} /></Form.Item>
            </Space>
            <Space wrap className="editor-actions">
              <Button icon={<SaveOutlined />} onClick={saveDraft}>保存草稿</Button>
              <Button type="primary" icon={<CheckOutlined />} onClick={approve}>通过入库</Button>
              <Button danger icon={<CloseOutlined />} onClick={reject}>驳回</Button>
              <Button icon={<SplitCellsOutlined />} onClick={splitQuestion}>拆分</Button>
              <Button icon={<MergeCellsOutlined />} onClick={mergeToPrevious}>合并上一题</Button>
            </Space>
          </Form>}
        </Card>
      </aside>
    </div>
  );
};

export default ReviewPage;
```

- [ ] **Step 2: Replace Review.css**

Replace `web-admin/src/pages/Review/Review.css`:

```css
.review-workspace { display: grid; grid-template-columns: 320px 1fr 460px; gap: 16px; padding: 16px; height: calc(100vh - 32px); background: #f5f5f5; }
.review-left, .review-middle, .review-right { min-height: 0; overflow: auto; }
.question-list-card { margin-top: 16px; }
.selected-batch, .selected-question { background: #eaf4ff; }
.q-list-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.q-list-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-preview { color: #999; text-align: center; padding: 80px 0; }
.preview-meta { margin-bottom: 12px; color: #666; }
.preview-ocr { background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 12px; max-height: 300px; overflow: auto; }
.preview-ocr pre { white-space: pre-wrap; margin: 0; }
.preview-images { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }
.preview-images img { max-width: 220px; max-height: 180px; object-fit: contain; border: 1px solid #eee; border-radius: 8px; background: #fff; }
.editor-actions { margin-top: 12px; }
```

- [ ] **Step 3: Commit**

```powershell
git add web-admin/src/pages/Review/Review.js web-admin/src/pages/Review/Review.css
git commit -m "feat(admin): add three-column parsed-question review workspace"
```

---

## Phase 6: Final Verification

### Task 12: Run full backend verification

**Files:**
- No source changes expected

- [ ] **Step 1: Run full backend tests**

```powershell
pytest -v
```

Expected: existing tests + new import tests all PASS.

- [ ] **Step 2: Reset and migrate dev DB**

Run from `backend`:

```powershell
python -c "from app import app; from models import db; ctx=app.app_context(); ctx.push(); db.create_all(); print('created tables')"
python migrate_import_recognition.py
```

Expected: no errors.

- [ ] **Step 3: Start backend**

Use existing stable runner if available:

```powershell
Start-Job -ScriptBlock { python "C:\bro-dev\runserver.py" }
```

If not available, run:

```powershell
python -c "from app import app; app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)"
```

- [ ] **Step 4: Curl smoke test single import**

```powershell
curl.exe -s -X POST http://127.0.0.1:5001/api/import/single -H "Content-Type: application/json" -d "{\"text\":\"1. 1+1=?`n答案：2\",\"exam_type\":\"gaokao\",\"subject\":\"数学\",\"grade\":\"高一\",\"knowledge_point\":\"计算\"}"
```

Expected JSON contains `"success":true` and `"total_questions":1`.

- [ ] **Step 5: Commit any verification doc if created**

No commit needed if no files changed.

---

## Self-Review

### Spec Coverage

- Single-question import: Task 7 `/api/import/single`, Task 10 Import UI single tab.
- Batch import: Task 7 `/api/import/batch`, Task 10 batch upload tab.
- PDF/Word/image/TXT: Task 4 DocumentIngestor.
- Text/formula/symbol/image recognition: Task 2 schema, Task 5 pipeline, Task 6 normalizer. First version has deterministic text baseline and image placeholders; OCR/AI hooks are isolated for later provider-specific enhancements.
- LaTeX + image fallback: Task 1 metadata, Task 2 formula schema, Task 11 editor field.
- Auto image association: Task 2 image schema and Task 4 image assets preserve page associations; advanced bbox proximity can be improved later behind same schema.
- Mandatory review: Task 7 imports create ParsedQuestion; Task 8 approval creates Question.
- Web-admin three-column review: Task 11.

### Placeholder Scan

No `TBD`, `TODO`, or undefined function names. External OCR/AI provider tuning is deliberately out of scope for this implementation phase.

### Type Consistency

- `QuestionCandidate.to_dict()` returns keys consumed by `QuestionNormalizer.to_parsed_payload()`.
- `_parsed_from_payload()` stores JSON arrays/objects as text fields matching model columns.
- web-admin API method names match backend endpoints.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-21-question-import-recognition-plan.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
