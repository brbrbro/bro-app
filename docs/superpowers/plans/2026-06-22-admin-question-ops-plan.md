# Admin Question Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first web-admin module for question-bank operations: import batches, review queue, official question bank management, quality checks, and import recognition stats.

**Architecture:** Add a new backend admin blueprint under `/api/admin/...` for operational queries/actions, while preserving existing `/api/import/...` review APIs. Upgrade the React web-admin sidebar into a grouped “题库运营” module with five routes. Keep this phase focused on question operations; feedback/errors, user management, and dashboards remain later phases.

**Tech Stack:** Flask 3.0 / SQLAlchemy / pytest / React 18 / Ant Design 5 / axios

---

## Existing Context

Project root: `E:\Opencode\越己\Bro app\bro-app`

Backend:
- `backend/models.py`: `ImportBatch`, `ParsedQuestion`, `Question`, `QuestionImage`
- `backend/routes/import.py`: single/batch import, review, split/merge/safe approve
- `backend/routes/questions.py`: user-facing question list/detail/random
- Tests currently pass: `pytest -q` → 70 passed

Web-admin:
- `web-admin/src/App.js`: current routes `/`, `/review`, `/bank`
- `web-admin/src/pages/Import/Import.js`: single + batch upload UI
- `web-admin/src/pages/Review/Review.js`: three-column parsed-question review workspace
- `web-admin/src/pages/QuestionBank/QuestionBank.js`: placeholder table; data loading not implemented
- `web-admin/src/services/api.js`: import/review API methods

---

## File Structure

```text
backend/
├── routes/
│   ├── __init__.py                    Modify: register admin_bp
│   └── admin.py                       Create: all /api/admin endpoints
└── tests/
    └── test_admin_question_ops.py     Create: admin API tests

web-admin/src/
├── App.js                             Modify: grouped question-ops navigation/routes
├── services/api.js                    Modify: admin API client methods
└── pages/
    └── QuestionOps/
        ├── ImportBatches.js           Create: batch management page
        ├── ImportBatches.css          Create
        ├── QuestionBankOps.js         Create: official question management page
        ├── QuestionBankOps.css        Create
        ├── QualityIssues.js           Create: issue list page
        ├── QualityIssues.css          Create
        ├── ImportStats.js             Create: stats page
        └── ImportStats.css            Create
```

---

## Task 1: Backend admin blueprint scaffold

**Files:**
- Modify: `backend/routes/__init__.py`
- Create: `backend/routes/admin.py`
- Create: `backend/tests/test_admin_question_ops.py`

- [ ] **Step 1: Write failing health/scaffold tests**

Create `backend/tests/test_admin_question_ops.py`:

```python
import json
from datetime import datetime, timezone, timedelta


def test_admin_import_batches_empty(client):
    resp = client.get('/api/admin/import/batches')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['batches'] == []
    assert data['total'] == 0


def test_admin_import_stats_empty(client):
    resp = client.get('/api/admin/import/stats')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['totals']['batches'] == 0
    assert data['totals']['parsed_questions'] == 0
```

- [ ] **Step 2: Run failing tests**

Run from `backend`:

```powershell
pytest tests/test_admin_question_ops.py::test_admin_import_batches_empty tests/test_admin_question_ops.py::test_admin_import_stats_empty -v
```

Expected: FAIL with 404 because `/api/admin/...` does not exist.

- [ ] **Step 3: Register admin blueprint**

Modify `backend/routes/__init__.py`:

Add near other blueprints:

```python
admin_bp = Blueprint('admin', __name__)
```

Add `admin` to the imports inside `register_blueprints` and register:

```python
app.register_blueprint(admin_bp, url_prefix='/api/admin')
```

The final function should still register all existing blueprints.

- [ ] **Step 4: Create `backend/routes/admin.py`**

```python
import json
from datetime import datetime, timezone
from flask import jsonify, request
from sqlalchemy import func
from models import db, ImportBatch, ParsedQuestion, Question
from . import admin_bp


def _parse_date(value):
    if not value:
        return None
    return datetime.fromisoformat(value)


def _batch_to_dict(batch):
    low_confidence_count = ParsedQuestion.query.filter(
        ParsedQuestion.batch_id == batch.id,
        ParsedQuestion.confidence < 0.85
    ).count()
    parsed = batch.parsed_questions or 0
    approved = batch.approved_questions or 0
    success_rate = round(approved / parsed, 3) if parsed else 0
    return {
        'id': batch.id,
        'source_type': batch.source_type,
        'source_file': batch.source_file,
        'status': batch.status,
        'exam_type': batch.exam_type,
        'subject': batch.subject,
        'grade': batch.grade,
        'knowledge_point': batch.knowledge_point,
        'total_questions': batch.total_questions or 0,
        'parsed_questions': parsed,
        'approved_questions': approved,
        'success_rate': success_rate,
        'low_confidence_count': low_confidence_count,
        'created_at': batch.created_at.isoformat() if batch.created_at else '',
        'failure_reason': '解析失败' if batch.status in ('failed', 'error') else ''
    }


@admin_bp.route('/import/batches', methods=['GET'])
def admin_import_batches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    subject = request.args.get('subject')
    source_type = request.args.get('source_type')
    start_date = _parse_date(request.args.get('start_date'))
    end_date = _parse_date(request.args.get('end_date'))

    q = ImportBatch.query
    if status:
        q = q.filter_by(status=status)
    if subject:
        q = q.filter_by(subject=subject)
    if source_type:
        q = q.filter_by(source_type=source_type)
    if start_date:
        q = q.filter(ImportBatch.created_at >= start_date)
    if end_date:
        q = q.filter(ImportBatch.created_at <= end_date)

    pagination = q.order_by(ImportBatch.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'batches': [_batch_to_dict(b) for b in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@admin_bp.route('/import/stats', methods=['GET'])
def admin_import_stats():
    batches = ImportBatch.query.all()
    total_batches = len(batches)
    total_parsed = sum(b.parsed_questions or 0 for b in batches)
    total_approved = sum(b.approved_questions or 0 for b in batches)
    failed_batches = sum(1 for b in batches if b.status in ('failed', 'error'))
    avg_questions = round(total_parsed / total_batches, 2) if total_batches else 0

    confidences = [p.confidence for p in ParsedQuestion.query.all() if p.confidence is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0
    low_confidence = ParsedQuestion.query.filter(ParsedQuestion.confidence < 0.85).count()

    return jsonify({
        'totals': {
            'batches': total_batches,
            'parsed_questions': total_parsed,
            'approved_questions': total_approved,
            'approval_rate': round(total_approved / total_parsed, 3) if total_parsed else 0,
            'average_confidence': avg_confidence,
            'low_confidence_count': low_confidence,
            'failed_batches': failed_batches,
            'average_questions_per_batch': avg_questions
        },
        'by_status': _group_batches('status'),
        'by_subject': _group_batches('subject'),
        'by_source_type': _group_batches('source_type')
    })


def _group_batches(field):
    col = getattr(ImportBatch, field)
    rows = db.session.query(col, func.count(ImportBatch.id)).group_by(col).all()
    return [{'key': key or '未设置', 'count': count} for key, count in rows]
```

- [ ] **Step 5: Run tests**

```powershell
pytest tests/test_admin_question_ops.py::test_admin_import_batches_empty tests/test_admin_question_ops.py::test_admin_import_stats_empty -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend/routes/__init__.py backend/routes/admin.py backend/tests/test_admin_question_ops.py
git commit -m "feat(admin): add admin blueprint with import batch list and stats scaffold"
```

---

## Task 2: Admin import batch detail/delete/reparse APIs

**Files:**
- Modify: `backend/routes/admin.py`
- Modify: `backend/tests/test_admin_question_ops.py`

- [ ] **Step 1: Add failing tests**

Append to `backend/tests/test_admin_question_ops.py`:

```python

def _make_batch(app, status='reviewing'):
    from models import db, ImportBatch, ParsedQuestion
    with app.app_context():
        batch = ImportBatch(
            source_type='txt', source_file='sample.txt', source_url='', status=status,
            exam_type='gaokao', subject='数学', grade='高一', knowledge_point='计算',
            total_questions=2, parsed_questions=2, approved_questions=1
        )
        db.session.add(batch)
        db.session.commit()
        pq = ParsedQuestion(
            batch_id=batch.id, raw_content='{}', content='1+1=?', options='[]',
            answer='2', explanation='', exam_type='gaokao', subject='数学', grade='高一',
            knowledge_point='计算', type='blank', difficulty=1, confidence=0.9, status='pending'
        )
        db.session.add(pq)
        db.session.commit()
        return batch.id


def test_admin_import_batch_detail(client, app):
    batch_id = _make_batch(app)
    resp = client.get(f'/api/admin/import/batches/{batch_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['id'] == batch_id
    assert data['parsed_questions'] == 2


def test_admin_delete_batch_deletes_parsed_only(client, app):
    from models import ParsedQuestion
    batch_id = _make_batch(app)
    resp = client.delete(f'/api/admin/import/batches/{batch_id}')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    with app.app_context():
        assert ParsedQuestion.query.filter_by(batch_id=batch_id).count() == 0


def test_admin_reparse_missing_source_returns_400(client, app):
    batch_id = _make_batch(app)
    resp = client.post(f'/api/admin/import/batches/{batch_id}/reparse')
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'source_file_missing'
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_admin_question_ops.py::test_admin_import_batch_detail tests/test_admin_question_ops.py::test_admin_delete_batch_deletes_parsed_only tests/test_admin_question_ops.py::test_admin_reparse_missing_source_returns_400 -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Add routes to `backend/routes/admin.py`**

Append:

```python
@admin_bp.route('/import/batches/<int:batch_id>', methods=['GET'])
def admin_import_batch_detail(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(_batch_to_dict(batch))


@admin_bp.route('/import/batches/<int:batch_id>', methods=['DELETE'])
def admin_delete_import_batch(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    ParsedQuestion.query.filter_by(batch_id=batch_id).delete(synchronize_session=False)
    db.session.delete(batch)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/import/batches/<int:batch_id>/reparse', methods=['POST'])
def admin_reparse_import_batch(batch_id):
    batch = db.session.get(ImportBatch, batch_id)
    if not batch:
        return jsonify({'error': 'not_found'}), 404
    if not batch.source_url:
        return jsonify({'error': 'source_file_missing'}), 400
    import os
    if not os.path.exists(batch.source_url):
        return jsonify({'error': 'source_file_missing'}), 400
    return jsonify({'success': False, 'error': 'reparse_requires_worker'}), 400
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_admin_question_ops.py -v
```

Expected: all tests in file pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/routes/admin.py backend/tests/test_admin_question_ops.py
git commit -m "feat(admin): add import batch detail delete and reparse endpoints"
```

---

## Task 3: Admin question bank APIs

**Files:**
- Modify: `backend/routes/admin.py`
- Modify: `backend/tests/test_admin_question_ops.py`

- [ ] **Step 1: Add failing tests**

Append:

```python

def _make_question(app, content='1+1=?', subject='数学', status='approved'):
    from models import db, Question
    with app.app_context():
        q = Question(
            region='mainland', subject=subject, grade='高一', knowledge_point='计算',
            type='blank', difficulty=1, content=content, answer='2', explanation='基础计算',
            options='[]', source='seed', status=status
        )
        db.session.add(q)
        db.session.commit()
        return q.id


def test_admin_questions_list_filter_keyword(client, app):
    _make_question(app, content='苹果题')
    _make_question(app, content='香蕉题')
    resp = client.get('/api/admin/questions?keyword=苹果')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 1
    assert '苹果' in data['questions'][0]['content']


def test_admin_question_detail_and_update(client, app):
    qid = _make_question(app)
    detail = client.get(f'/api/admin/questions/{qid}')
    assert detail.status_code == 200
    resp = client.put(f'/api/admin/questions/{qid}', json={'answer': '二', 'difficulty': 2})
    assert resp.status_code == 200
    assert resp.get_json()['question']['answer'] == '二'
    assert resp.get_json()['question']['difficulty'] == 2


def test_admin_question_archive_and_delete(client, app):
    qid = _make_question(app)
    archive = client.post(f'/api/admin/questions/{qid}/archive')
    assert archive.status_code == 200
    assert archive.get_json()['question']['status'] == 'archived'
    delete = client.delete(f'/api/admin/questions/{qid}')
    assert delete.status_code == 200
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_admin_question_ops.py::test_admin_questions_list_filter_keyword tests/test_admin_question_ops.py::test_admin_question_detail_and_update tests/test_admin_question_ops.py::test_admin_question_archive_and_delete -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Add question serializer and routes**

Append to `backend/routes/admin.py`:

```python
def _question_to_dict(q):
    return {
        'id': q.id,
        'region': q.region,
        'subject': q.subject,
        'grade': q.grade,
        'syllabus': q.syllabus,
        'knowledge_point': q.knowledge_point,
        'type': q.type,
        'difficulty': q.difficulty,
        'content': q.content,
        'answer': q.answer,
        'explanation': q.explanation,
        'options': json.loads(q.options) if q.options else [],
        'source': q.source,
        'status': q.status,
        'solved_count': q.solved_count or 0,
        'correct_rate': q.correct_rate or 0,
        'created_at': q.created_at.isoformat() if q.created_at else ''
    }


@admin_bp.route('/questions', methods=['GET'])
def admin_questions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword')
    q = Question.query
    for field in ['subject', 'grade', 'knowledge_point', 'type', 'source', 'status']:
        value = request.args.get(field)
        if value:
            q = q.filter(getattr(Question, field) == value)
    difficulty = request.args.get('difficulty', type=int)
    if difficulty:
        q = q.filter(Question.difficulty == difficulty)
    if keyword:
        q = q.filter(Question.content.contains(keyword))
    pagination = q.order_by(Question.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({'questions': [_question_to_dict(item) for item in pagination.items], 'total': pagination.total, 'page': page, 'pages': pagination.pages})


@admin_bp.route('/questions/<int:question_id>', methods=['GET'])
def admin_question_detail(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(_question_to_dict(q))


@admin_bp.route('/questions/<int:question_id>', methods=['PUT'])
def admin_update_question(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    data = request.get_json() or {}
    for field in ['content', 'answer', 'explanation', 'subject', 'grade', 'knowledge_point', 'type', 'difficulty', 'status']:
        if field in data:
            setattr(q, field, data[field])
    if 'options' in data:
        q.options = json.dumps(data.get('options', []), ensure_ascii=False)
    db.session.commit()
    return jsonify({'success': True, 'question': _question_to_dict(q)})


@admin_bp.route('/questions/<int:question_id>/archive', methods=['POST'])
def admin_archive_question(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    q.status = 'archived'
    db.session.commit()
    return jsonify({'success': True, 'question': _question_to_dict(q)})


@admin_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def admin_delete_question(question_id):
    q = db.session.get(Question, question_id)
    if not q:
        return jsonify({'error': 'not_found'}), 404
    db.session.delete(q)
    db.session.commit()
    return jsonify({'success': True})
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_admin_question_ops.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/routes/admin.py backend/tests/test_admin_question_ops.py
git commit -m "feat(admin): add question bank management APIs"
```

---

## Task 4: Admin quality issue API

**Files:**
- Modify: `backend/routes/admin.py`
- Modify: `backend/tests/test_admin_question_ops.py`

- [ ] **Step 1: Add failing quality tests**

Append:

```python

def test_admin_quality_detects_missing_answer_and_explanation(client, app):
    _make_question(app, content='缺答案题')
    from models import db, Question
    with app.app_context():
        q = Question.query.filter_by(content='缺答案题').first()
        q.answer = ''
        q.explanation = ''
        db.session.commit()
    resp = client.get('/api/admin/quality/issues')
    assert resp.status_code == 200
    issue_types = [i['issue_type'] for i in resp.get_json()['issues']]
    assert 'missing_answer' in issue_types
    assert 'missing_explanation' in issue_types


def test_admin_quality_detects_duplicate_content(client, app):
    _make_question(app, content='重复题')
    _make_question(app, content='重复题')
    resp = client.get('/api/admin/quality/issues?issue_type=duplicate_content')
    assert resp.status_code == 200
    assert resp.get_json()['issues'][0]['issue_type'] == 'duplicate_content'
```

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests/test_admin_question_ops.py::test_admin_quality_detects_missing_answer_and_explanation tests/test_admin_question_ops.py::test_admin_quality_detects_duplicate_content -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Add quality route**

Append to `backend/routes/admin.py`:

```python
def _issue(issue_type, severity, question, suggestion):
    return {
        'issue_type': issue_type,
        'severity': severity,
        'question_id': question.id,
        'content': question.content,
        'subject': question.subject,
        'suggestion': suggestion
    }


@admin_bp.route('/quality/issues', methods=['GET'])
def admin_quality_issues():
    issue_filter = request.args.get('issue_type')
    issues = []
    questions = Question.query.all()

    for q in questions:
        if not q.answer:
            issues.append(_issue('missing_answer', 'high', q, '补充答案'))
        if not q.explanation:
            issues.append(_issue('missing_explanation', 'medium', q, '补充解析'))
        if q.type == 'choice':
            try:
                options = json.loads(q.options) if q.options else []
            except Exception:
                options = []
            if len(options) < 2:
                issues.append(_issue('invalid_options', 'high', q, '补充至少两个选项'))
        if not q.type or q.type == 'unknown':
            issues.append(_issue('unknown_type', 'medium', q, '设置题型'))
        if not q.subject or not q.knowledge_point:
            issues.append(_issue('missing_taxonomy', 'medium', q, '补充科目和知识点'))

    duplicate_rows = db.session.query(Question.content, func.count(Question.id)).group_by(Question.content).having(func.count(Question.id) > 1).all()
    duplicate_contents = {row[0] for row in duplicate_rows}
    for q in questions:
        if q.content in duplicate_contents:
            issues.append(_issue('duplicate_content', 'medium', q, '检查是否重复题'))

    low_confidence = ParsedQuestion.query.filter(ParsedQuestion.status == 'pending', ParsedQuestion.confidence < 0.85).all()
    for p in low_confidence:
        issues.append({
            'issue_type': 'low_confidence_import',
            'severity': 'medium',
            'parsed_question_id': p.id,
            'content': p.content,
            'subject': p.subject,
            'suggestion': '人工复核低置信识别结果'
        })

    if issue_filter:
        issues = [i for i in issues if i['issue_type'] == issue_filter]

    return jsonify({'issues': issues, 'total': len(issues)})
```

- [ ] **Step 4: Run tests**

```powershell
pytest tests/test_admin_question_ops.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/routes/admin.py backend/tests/test_admin_question_ops.py
git commit -m "feat(admin): add question quality issue API"
```

---

## Task 5: Admin import statistics groupings

**Files:**
- Modify: `backend/routes/admin.py`
- Modify: `backend/tests/test_admin_question_ops.py`

- [ ] **Step 1: Add stats tests**

Append:

```python

def test_admin_import_stats_counts_batches(client, app):
    _make_batch(app, status='reviewing')
    _make_batch(app, status='completed')
    resp = client.get('/api/admin/import/stats')
    assert resp.status_code == 200
    totals = resp.get_json()['totals']
    assert totals['batches'] == 2
    assert totals['parsed_questions'] == 4
    assert totals['approved_questions'] == 2
    assert 'by_status' in resp.get_json()
```

- [ ] **Step 2: Run test**

```powershell
pytest tests/test_admin_question_ops.py::test_admin_import_stats_counts_batches -v
```

Expected: PASS if Task 1 stats already sufficient. If it fails, fix stats calculation.

- [ ] **Step 3: Commit if changed**

If only test added:

```powershell
git add backend/tests/test_admin_question_ops.py
git commit -m "test(admin): cover import statistics totals"
```

---

## Task 6: Web-admin API client methods

**Files:**
- Modify: `web-admin/src/services/api.js`

- [ ] **Step 1: Extend API client**

Append the following exports before `export default api;`:

```javascript
export const getAdminBatches = (params = {}) => api.get('/admin/import/batches', { params });
export const getAdminBatch = (id) => api.get(`/admin/import/batches/${id}`);
export const deleteAdminBatch = (id) => api.delete(`/admin/import/batches/${id}`);
export const reparseAdminBatch = (id) => api.post(`/admin/import/batches/${id}/reparse`);

export const getAdminQuestions = (params = {}) => api.get('/admin/questions', { params });
export const getAdminQuestion = (id) => api.get(`/admin/questions/${id}`);
export const updateAdminQuestion = (id, data) => api.put(`/admin/questions/${id}`, data);
export const archiveAdminQuestion = (id) => api.post(`/admin/questions/${id}/archive`);
export const deleteAdminQuestion = (id) => api.delete(`/admin/questions/${id}`);

export const getQualityIssues = (params = {}) => api.get('/admin/quality/issues', { params });
export const getImportStats = (params = {}) => api.get('/admin/import/stats', { params });
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/services/api.js
git commit -m "feat(admin): add question ops API client methods"
```

---

## Task 7: Web-admin routing and navigation

**Files:**
- Modify: `web-admin/src/App.js`

- [ ] **Step 1: Replace App.js**

Replace `web-admin/src/App.js` with:

```javascript
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  UploadOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  WarningOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import ImportPage from './pages/Import/Import';
import ReviewPage from './pages/Review/Review';
import ImportBatchesPage from './pages/QuestionOps/ImportBatches';
import QuestionBankOpsPage from './pages/QuestionOps/QuestionBankOps';
import QualityIssuesPage from './pages/QuestionOps/QualityIssues';
import ImportStatsPage from './pages/QuestionOps/ImportStats';

const { Header, Sider, Content } = Layout;

function AdminLayout() {
  const location = useLocation();
  const selectedKey = location.pathname;
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={220}>
        <div style={{ padding: '16px', fontSize: '18px', fontWeight: 'bold', textAlign: 'center' }}>
          BRO 管理后台
        </div>
        <Menu mode="inline" selectedKeys={[selectedKey]} defaultOpenKeys={['ops']} items={[
          {
            key: 'ops',
            label: '题库运营',
            type: 'group',
            children: [
              { key: '/ops/import-batches', icon: <UploadOutlined />, label: <Link to="/ops/import-batches">导入批次</Link> },
              { key: '/ops/review', icon: <CheckCircleOutlined />, label: <Link to="/ops/review">审核队列</Link> },
              { key: '/ops/questions', icon: <DatabaseOutlined />, label: <Link to="/ops/questions">题库管理</Link> },
              { key: '/ops/quality', icon: <WarningOutlined />, label: <Link to="/ops/quality">质量检查</Link> },
              { key: '/ops/stats', icon: <BarChartOutlined />, label: <Link to="/ops/stats">识别统计</Link> }
            ]
          }
        ]} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', fontSize: '18px' }}>
          题库运营后台
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/ops/import-batches" replace />} />
            <Route path="/ops/import-batches" element={<ImportBatchesPage />} />
            <Route path="/ops/review" element={<ReviewPage />} />
            <Route path="/ops/questions" element={<QuestionBankOpsPage />} />
            <Route path="/ops/quality" element={<QualityIssuesPage />} />
            <Route path="/ops/stats" element={<ImportStatsPage />} />
            <Route path="/import" element={<ImportPage />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/bank" element={<QuestionBankOpsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

function App() {
  return <Router><AdminLayout /></Router>;
}

export default App;
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/App.js
git commit -m "feat(admin): add question operations navigation routes"
```

---

## Task 8: ImportBatches page

**Files:**
- Create: `web-admin/src/pages/QuestionOps/ImportBatches.js`
- Create: `web-admin/src/pages/QuestionOps/ImportBatches.css`

- [ ] **Step 1: Create page**

Create `web-admin/src/pages/QuestionOps/ImportBatches.js`:

```javascript
import React, { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { DeleteOutlined, ReloadOutlined, SearchOutlined, EyeOutlined } from '@ant-design/icons';
import { deleteAdminBatch, getAdminBatches, reparseAdminBatch } from '../../services/api';
import './ImportBatches.css';

const { Option } = Select;

const ImportBatchesPage = () => {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ page: 1, per_page: 20 });

  const load = async (next = filters) => {
    setLoading(true);
    try {
      const res = await getAdminBatches(next);
      setRows(res.data.batches || []);
      setTotal(res.data.total || 0);
      setFilters(next);
    } catch (e) {
      message.error('加载批次失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    await deleteAdminBatch(id);
    message.success('已删除批次');
    load();
  };

  const reparse = async (id) => {
    try {
      await reparseAdminBatch(id);
      message.success('已提交重新解析');
      load();
    } catch (e) {
      message.error(e.response?.data?.error || '重新解析失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 70 },
    { title: '文件', dataIndex: 'source_file', ellipsis: true },
    { title: '类型', dataIndex: 'source_type', width: 90 },
    { title: '科目', dataIndex: 'subject', width: 100 },
    { title: '状态', dataIndex: 'status', width: 110, render: v => <Tag>{v}</Tag> },
    { title: '题数', render: r => `${r.parsed_questions}/${r.total_questions}`, width: 110 },
    { title: '通过', dataIndex: 'approved_questions', width: 80 },
    { title: '低置信', dataIndex: 'low_confidence_count', width: 90 },
    { title: '成功率', dataIndex: 'success_rate', width: 90, render: v => `${Math.round((v || 0) * 100)}%` },
    { title: '创建时间', dataIndex: 'created_at', width: 180 },
    {
      title: '操作', width: 240, render: (_, r) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => window.location.href = `/ops/review?batch=${r.id}`}>审核</Button>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => reparse(r.id)}>重解析</Button>
          <Popconfirm title="确定删除该批次？" onConfirm={() => remove(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <Card title="导入批次" className="ops-card">
      <Form layout="inline" className="ops-filter">
        <Form.Item label="状态"><Select allowClear style={{ width: 140 }} onChange={v => setFilters({ ...filters, status: v, page: 1 })}><Option value="reviewing">reviewing</Option><Option value="completed">completed</Option><Option value="failed">failed</Option><Option value="processing">processing</Option></Select></Form.Item>
        <Form.Item label="科目"><Input style={{ width: 120 }} onChange={e => setFilters({ ...filters, subject: e.target.value, page: 1 })} /></Form.Item>
        <Form.Item label="类型"><Input style={{ width: 120 }} onChange={e => setFilters({ ...filters, source_type: e.target.value, page: 1 })} /></Form.Item>
        <Button type="primary" icon={<SearchOutlined />} onClick={() => load({ ...filters, page: 1 })}>查询</Button>
      </Form>
      <Table rowKey="id" loading={loading} dataSource={rows} columns={columns} pagination={{ current: filters.page, pageSize: filters.per_page, total, onChange: page => load({ ...filters, page }) }} />
    </Card>
  );
};

export default ImportBatchesPage;
```

Create `web-admin/src/pages/QuestionOps/ImportBatches.css`:

```css
.ops-card { min-height: 70vh; }
.ops-filter { margin-bottom: 16px; row-gap: 12px; }
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/pages/QuestionOps/ImportBatches.js web-admin/src/pages/QuestionOps/ImportBatches.css
git commit -m "feat(admin): add import batch operations page"
```

---

## Task 9: QuestionBankOps page

**Files:**
- Create: `web-admin/src/pages/QuestionOps/QuestionBankOps.js`
- Create: `web-admin/src/pages/QuestionOps/QuestionBankOps.css`

- [ ] **Step 1: Create page**

Create `web-admin/src/pages/QuestionOps/QuestionBankOps.js`:

```javascript
import React, { useEffect, useState } from 'react';
import { Button, Card, Drawer, Form, Input, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { DeleteOutlined, EditOutlined, SearchOutlined, StopOutlined } from '@ant-design/icons';
import { archiveAdminQuestion, deleteAdminQuestion, getAdminQuestions, updateAdminQuestion } from '../../services/api';
import './QuestionBankOps.css';

const { TextArea } = Input;
const { Option } = Select;

const QuestionBankOpsPage = () => {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ page: 1, per_page: 20 });
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();

  const load = async (next = filters) => {
    setLoading(true);
    try {
      const res = await getAdminQuestions(next);
      setRows(res.data.questions || []);
      setTotal(res.data.total || 0);
      setFilters(next);
    } catch (e) {
      message.error('加载题库失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openEdit = (record) => {
    setEditing(record);
    form.setFieldsValue({ ...record, options: (record.options || []).map(o => typeof o === 'string' ? o : `${o.key || ''}. ${o.text || ''}`).join('\n') });
  };

  const save = async () => {
    const values = await form.validateFields();
    await updateAdminQuestion(editing.id, { ...values, options: (values.options || '').split('\n').filter(Boolean) });
    message.success('已保存');
    setEditing(null);
    load();
  };

  const archive = async (id) => { await archiveAdminQuestion(id); message.success('已下架'); load(); };
  const remove = async (id) => { await deleteAdminQuestion(id); message.success('已删除'); load(); };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 70 },
    { title: '科目', dataIndex: 'subject', width: 100 },
    { title: '年级', dataIndex: 'grade', width: 100 },
    { title: '知识点', dataIndex: 'knowledge_point', width: 140 },
    { title: '类型', dataIndex: 'type', width: 90 },
    { title: '难度', dataIndex: 'difficulty', width: 80 },
    { title: '来源', dataIndex: 'source', width: 100 },
    { title: '状态', dataIndex: 'status', width: 100, render: v => <Tag>{v}</Tag> },
    { title: '内容', dataIndex: 'content', ellipsis: true },
    {
      title: '操作', width: 210, render: (_, r) => <Space>
        <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
        <Button size="small" icon={<StopOutlined />} onClick={() => archive(r.id)}>下架</Button>
        <Popconfirm title="确定删除该题？" onConfirm={() => remove(r.id)}><Button size="small" danger icon={<DeleteOutlined />}>删除</Button></Popconfirm>
      </Space>
    }
  ];

  return <Card title="题库管理" className="ops-card">
    <Form layout="inline" className="ops-filter">
      <Input placeholder="关键词" style={{ width: 180 }} onChange={e => setFilters({ ...filters, keyword: e.target.value, page: 1 })} />
      <Input placeholder="科目" style={{ width: 120 }} onChange={e => setFilters({ ...filters, subject: e.target.value, page: 1 })} />
      <Input placeholder="年级" style={{ width: 120 }} onChange={e => setFilters({ ...filters, grade: e.target.value, page: 1 })} />
      <Input placeholder="知识点" style={{ width: 160 }} onChange={e => setFilters({ ...filters, knowledge_point: e.target.value, page: 1 })} />
      <Select placeholder="题型" allowClear style={{ width: 130 }} onChange={v => setFilters({ ...filters, type: v, page: 1 })}><Option value="choice">选择题</Option><Option value="blank">填空题</Option><Option value="comprehensive">解答题</Option><Option value="unknown">未知</Option></Select>
      <Button type="primary" icon={<SearchOutlined />} onClick={() => load({ ...filters, page: 1 })}>搜索</Button>
    </Form>
    <Table rowKey="id" loading={loading} dataSource={rows} columns={columns} pagination={{ current: filters.page, pageSize: filters.per_page, total, onChange: page => load({ ...filters, page }) }} />
    <Drawer title="编辑题目" open={!!editing} width={720} onClose={() => setEditing(null)} extra={<Button type="primary" onClick={save}>保存</Button>}>
      <Form form={form} layout="vertical">
        <Form.Item label="题干" name="content" rules={[{ required: true }]}><TextArea rows={5} /></Form.Item>
        <Form.Item label="选项" name="options"><TextArea rows={4} /></Form.Item>
        <Form.Item label="答案" name="answer"><Input /></Form.Item>
        <Form.Item label="解析" name="explanation"><TextArea rows={4} /></Form.Item>
        <Space wrap>
          <Form.Item label="科目" name="subject"><Input /></Form.Item>
          <Form.Item label="年级" name="grade"><Input /></Form.Item>
          <Form.Item label="知识点" name="knowledge_point"><Input /></Form.Item>
          <Form.Item label="题型" name="type"><Input /></Form.Item>
          <Form.Item label="难度" name="difficulty"><Input type="number" /></Form.Item>
          <Form.Item label="状态" name="status"><Input /></Form.Item>
        </Space>
      </Form>
    </Drawer>
  </Card>;
};

export default QuestionBankOpsPage;
```

Create `web-admin/src/pages/QuestionOps/QuestionBankOps.css`:

```css
.ops-card { min-height: 70vh; }
.ops-filter { margin-bottom: 16px; gap: 8px; row-gap: 12px; }
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/pages/QuestionOps/QuestionBankOps.js web-admin/src/pages/QuestionOps/QuestionBankOps.css
git commit -m "feat(admin): add official question bank operations page"
```

---

## Task 10: QualityIssues page

**Files:**
- Create: `web-admin/src/pages/QuestionOps/QualityIssues.js`
- Create: `web-admin/src/pages/QuestionOps/QualityIssues.css`

- [ ] **Step 1: Create page**

Create `web-admin/src/pages/QuestionOps/QualityIssues.js`:

```javascript
import React, { useEffect, useState } from 'react';
import { Button, Card, Select, Table, Tag, message } from 'antd';
import { getQualityIssues } from '../../services/api';
import './QualityIssues.css';

const { Option } = Select;

const QualityIssuesPage = () => {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [issueType, setIssueType] = useState();

  const load = async (type = issueType) => {
    setLoading(true);
    try {
      const res = await getQualityIssues(type ? { issue_type: type } : {});
      setIssues(res.data.issues || []);
    } catch (e) {
      message.error('加载质量问题失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const columns = [
    { title: '类型', dataIndex: 'issue_type', width: 180, render: v => <Tag color="orange">{v}</Tag> },
    { title: '严重度', dataIndex: 'severity', width: 100, render: v => <Tag color={v === 'high' ? 'red' : 'gold'}>{v}</Tag> },
    { title: '题目ID', dataIndex: 'question_id', width: 90 },
    { title: '解析题ID', dataIndex: 'parsed_question_id', width: 100 },
    { title: '科目', dataIndex: 'subject', width: 100 },
    { title: '内容', dataIndex: 'content', ellipsis: true },
    { title: '建议', dataIndex: 'suggestion', width: 180 },
    { title: '操作', width: 120, render: (_, r) => <Button size="small" onClick={() => window.location.href = r.question_id ? `/ops/questions?keyword=${r.question_id}` : '/ops/review'}>打开</Button> }
  ];

  return <Card title="质量检查" className="ops-card">
    <div className="ops-filter">
      <Select allowClear placeholder="问题类型" style={{ width: 240 }} value={issueType} onChange={v => { setIssueType(v); load(v); }}>
        <Option value="missing_answer">缺答案</Option>
        <Option value="missing_explanation">缺解析</Option>
        <Option value="invalid_options">选项异常</Option>
        <Option value="duplicate_content">重复题</Option>
        <Option value="unknown_type">未知题型</Option>
        <Option value="missing_taxonomy">缺科目/知识点</Option>
        <Option value="low_confidence_import">低置信导入题</Option>
      </Select>
      <Button onClick={() => load()}>刷新扫描</Button>
    </div>
    <Table rowKey={(r, i) => `${r.issue_type}-${r.question_id || r.parsed_question_id}-${i}`} loading={loading} dataSource={issues} columns={columns} pagination={{ pageSize: 20 }} />
  </Card>;
};

export default QualityIssuesPage;
```

Create `web-admin/src/pages/QuestionOps/QualityIssues.css`:

```css
.ops-card { min-height: 70vh; }
.ops-filter { display: flex; gap: 8px; margin-bottom: 16px; }
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/pages/QuestionOps/QualityIssues.js web-admin/src/pages/QuestionOps/QualityIssues.css
git commit -m "feat(admin): add question quality issues page"
```

---

## Task 11: ImportStats page

**Files:**
- Create: `web-admin/src/pages/QuestionOps/ImportStats.js`
- Create: `web-admin/src/pages/QuestionOps/ImportStats.css`

- [ ] **Step 1: Create page**

Create `web-admin/src/pages/QuestionOps/ImportStats.js`:

```javascript
import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, message } from 'antd';
import { getImportStats } from '../../services/api';
import './ImportStats.css';

const ImportStatsPage = () => {
  const [stats, setStats] = useState({ totals: {}, by_status: [], by_subject: [], by_source_type: [] });

  useEffect(() => {
    getImportStats()
      .then(res => setStats(res.data))
      .catch(() => message.error('加载识别统计失败'));
  }, []);

  const cols = [{ title: '分组', dataIndex: 'key' }, { title: '数量', dataIndex: 'count' }];
  const t = stats.totals || {};

  return <div className="stats-page">
    <Row gutter={16} className="stats-row">
      <Col span={6}><Card><Statistic title="导入批次" value={t.batches || 0} /></Card></Col>
      <Col span={6}><Card><Statistic title="解析题数" value={t.parsed_questions || 0} /></Card></Col>
      <Col span={6}><Card><Statistic title="通过题数" value={t.approved_questions || 0} /></Card></Col>
      <Col span={6}><Card><Statistic title="通过率" value={Math.round((t.approval_rate || 0) * 100)} suffix="%" /></Card></Col>
    </Row>
    <Row gutter={16} className="stats-row">
      <Col span={6}><Card><Statistic title="平均置信度" value={Math.round((t.average_confidence || 0) * 100)} suffix="%" /></Card></Col>
      <Col span={6}><Card><Statistic title="低置信题" value={t.low_confidence_count || 0} /></Card></Col>
      <Col span={6}><Card><Statistic title="失败批次" value={t.failed_batches || 0} /></Card></Col>
      <Col span={6}><Card><Statistic title="平均每批题数" value={t.average_questions_per_batch || 0} /></Card></Col>
    </Row>
    <Row gutter={16}>
      <Col span={8}><Card title="按状态"><Table rowKey="key" size="small" dataSource={stats.by_status || []} columns={cols} pagination={false} /></Card></Col>
      <Col span={8}><Card title="按科目"><Table rowKey="key" size="small" dataSource={stats.by_subject || []} columns={cols} pagination={false} /></Card></Col>
      <Col span={8}><Card title="按文件类型"><Table rowKey="key" size="small" dataSource={stats.by_source_type || []} columns={cols} pagination={false} /></Card></Col>
    </Row>
  </div>;
};

export default ImportStatsPage;
```

Create `web-admin/src/pages/QuestionOps/ImportStats.css`:

```css
.stats-page { min-height: 70vh; }
.stats-row { margin-bottom: 16px; }
```

- [ ] **Step 2: Commit**

```powershell
git add web-admin/src/pages/QuestionOps/ImportStats.js web-admin/src/pages/QuestionOps/ImportStats.css
git commit -m "feat(admin): add import recognition statistics page"
```

---

## Task 12: Final verification

**Files:**
- No source changes expected

- [ ] **Step 1: Run backend tests**

```powershell
pytest -q
```

Expected: all backend tests pass.

- [ ] **Step 2: Build web-admin**

From `web-admin`:

```powershell
npm install
npm run build
```

Expected: production build succeeds.

- [ ] **Step 3: Commit lockfile if npm creates one**

If `package-lock.json` appears or changes:

```powershell
git add web-admin/package-lock.json
git commit -m "chore(admin): update web-admin lockfile"
```

---

## Self-Review

### Spec Coverage

- Import batch management: Tasks 1, 2, 8.
- Review queue: existing upgraded Review page retained; Task 7 routes it under `/ops/review`.
- Question bank management: Tasks 3, 6, 7, 9.
- Quality checks: Tasks 4, 6, 7, 10.
- Import statistics: Tasks 1, 5, 6, 7, 11.
- Tests: Tasks 1–5 backend pytest, Task 12 full verification.

### Placeholder Scan

No TBD/TODO placeholders. Admin auth and later modules are explicitly out of scope.

### Type Consistency

- Backend route paths match frontend API methods.
- Frontend route paths match App.js navigation.
- `Question` and `ImportBatch` fields used by admin serializers exist in `models.py`.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-22-admin-question-ops-plan.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
