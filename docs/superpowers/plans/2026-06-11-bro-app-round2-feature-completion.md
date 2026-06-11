# BRO App Round 2 — Execution Roadmap

> **For agentic workers:** This plan is the *roadmap*; per-task implementation details (full code, file paths, commit messages) are dispatched to subagents at execution time via `superpowers:subagent-driven-development`. Each batch below = 1 or more subagent invocations. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Execute 18 items from the action list (excluding #2 WeChat auth and #3 prod server — require external credentials). Cover: seed questions, engineering hygiene (SQLAlchemy 2.0/ESLint/CI), favorite loop, wrongbook cloud merge, streak UI, i18n, daily challenge 2x, difficulty filter, exchange, invite binding, leaderboard time dimension, lexicon corpus, notification backend, studyroom cloud sync, OCR/web-admin validation.

**Architecture:** Backend (Flask 3 + SQLAlchemy + JWT + pytest) — extend with 5 blueprints (seed loader, exchange, invite, lexicon, notification), add 3 models (ExchangeRecord, Invitation, Notification, LexiconWord). Mini-program — extend `utils/api.js` with ~10 methods; mostly modify existing pages, no new pages (except internal helpers).

**Tech Stack:** Python 3.12 / Flask 3.0 / SQLAlchemy 2.x / pytest 8.3 / WeChat Mini-Program native / GitHub Actions

---

## Project Conventions (subagents must know)

- Path: `E:\Opencode\越己\Bro app\bro-app`
- Backend dir: `backend/`; mini-program dir: `wechat-miniapp/`
- DB at `C:/bro-dev/bro.db`
- Test runner: `pytest -v` (workdir `backend`)
- Existing test count: 7 (will grow to ~25)
- git config already set: `brbrbro / brbrbro@users.noreply.github.com`
- Backend startup: `Start-Job -ScriptBlock { Set-Location "E:\Opencode\越己\Bro app\bro-app\backend"; python app.py }`
- Existing utils/api.js methods: request, getQuestions, getQuestion, getRandomQuestion, submitAnswer, submitProgress, getProgress, getWrongQuestions, getStats, getProfile, updateProfile, getMyQuestions, getLeaderboard, getCheckinStatus, doCheckin, getCheckinHistory
- Existing storage.js methods: STORAGE_KEYS, saveProgress, getProgress, getWrongQuestions, saveNote, getNotes, setUserInfo, getUserInfo, setSyncTime, getSyncTime, clearAll, addFavorite, removeFavorite, getFavorites, isFavorited
- Color palette: 主蓝 #4A90D9 / 辅蓝 #6BA8E8 / 红 #E74C3C / 绿 #2ECC71 / 橙 #F39C12 / 紫 #9B59B6 / 青 #1ABC9C / 金 #FFD700

---

## Skipped (Require Human Credentials)

- **Item #2** Real WeChat login — needs APPID + AppSecret
- **Item #3** Remote server recovery — needs SSH access to 106.53.188.248

---

## Execution Plan: 9 Batches

### Batch A — Seed Question Bank (item #1)
- [ ] **A.1** Create `backend/seeds/questions_seed.json` with 32 questions (8 per subject × 4: math/physics/chemistry/biology) following existing `Question` model schema. Difficulty 1-4 mix. All `region=mainland`, `status=approved`, `source=seed`.
- [ ] **A.2** Create `backend/seed_questions.py` (idempotent loader: skip if `subject+content` already exists) + `backend/tests/test_seed_loader.py` (3 tests: load JSON / import creates rows / dedup). Run loader. Commit.

**Acceptance:** `pytest tests/test_seed_loader.py` 3 passed; `python seed_questions.py` outputs `Seeded 32`; `curl /api/questions?subject=数学` returns total≥8.

---

### Batch B — Engineering Hygiene (items #18, #19, #20)
- [ ] **B.1** Fix all SQLAlchemy 2.0 deprecations: `User.query.get(id)` → `db.session.get(User, id)` in `routes/checkin.py`, `routes/users.py`, `routes/progress.py`; wrap `datetime.utcnow` in `_utc_now` helper in `models.py`. Re-run pytest. Commit.
- [ ] **B.2** Add `wechat-miniapp/.eslintrc.json` + `.eslintignore` with mini-program globals (wx/Page/App/Component/getApp). Commit.
- [ ] **B.3** Add `.github/workflows/backend-tests.yml` running pytest on push to backend/**. Commit.

**Acceptance:** pytest still 7+ passed with reduced deprecation warnings; CI yaml syntactically valid (push will trigger on next push).

---

### Batch C — Core Loop (items #4, #5, #9)
- [ ] **C.1** `wechat-miniapp/pages/practice/practice.{js,wxml,wxss}` — add ⭐/☆ toggle button calling `storage.addFavorite/removeFavorite/isFavorited`. State syncs on load. Commit.
- [ ] **C.2** `wechat-miniapp/pages/wrongbook/wrongbook.js` — if logged in, fetch `/api/progress/wrong` and merge IDs with local `storage.getProgress().filter(!is_correct).map(question_id)`, deduplicate, then `getQuestion(id)` each. Commit.
- [ ] **C.3** `wechat-miniapp/pages/index/index.{js,wxml,wxss}` — add `streak` to data, populate from `getCheckinStatus().streak` and `doCheckin().streak`. Display `🔥连N天` badge under sign-in button when streak>0. Commit.

**Acceptance:** Manual: open practice, click ⭐ → mybag shows it. Open wrongbook after answering wrong → shows merged list. Sign in → 🔥连1天 appears.

---

### Batch D — i18n Dictionary Expansion (item #8)
- [ ] **D.1** `wechat-miniapp/utils/i18n.js` — append ~80 keys to each of `translations.zh`, `translations.zht`, `translations.en` covering all 15 new pages (stats/myquestions/mybag/classmates/invite/membership/daily/leaderboard/points-shop/licitong/square/studyroom/notifications/difficulty/settings). Commit.

**Note:** This batch only adds the dictionary entries. Refactoring each page's hardcoded strings to use `i18n.t()` is out of scope — pages already work; this just enables future i18n switching.

**Acceptance:** All 3 languages have ~80 new keys parsed without syntax error. Verify with `node -e "console.log(Object.keys(require('./wechat-miniapp/utils/i18n.js').translations.zh).length)"` — should print ≥120.

---

### Batch E — Difficulty Filter & 2x Challenge (items #10, #17)
- [ ] **E.1** Backend: `routes/questions.py` `get_random_question` add `difficulty` query param. `routes/progress.py` `submit_progress` accept `is_challenge: bool` → if `is_correct and is_challenge` award `difficulty * 2` points (else `difficulty` points). Add 4 tests: difficulty filter / no match 404 / challenge doubles / normal awards base. Commit.
- [ ] **E.2** Mini-program: `pages/daily-challenge/daily-challenge.js` — `loadChallenge` reads `wx.getStorageSync('difficulty_pref')` and passes as param. `pages/practice/practice.js` — capture `?challenge=1` in `onLoad`, pass to `api.submitProgress({is_challenge})`, show toast `+N 积分` on response. Commit.

**Acceptance:** `pytest tests/test_difficulty_filter.py` 4 passed; manual: set difficulty=2 in 难度偏好, open 每日挑战 → backend gets difficulty=2; answer correctly → toast shows `+4 积分` (difficulty 2 × 2x).

---

### Batch F — Exchange & Invite (items #11, #12)
- [ ] **F.1** Backend models: append `ExchangeRecord` and `Invitation` to `backend/models.py`. Update `migrate_add_points.py` to create both tables. Run migration.
- [ ] **F.2** Backend routes: create `routes/exchange.py` (3 endpoints: GET /items, POST /, GET /history) and `routes/invite.py` (2 endpoints: POST /bind, GET /list). Register in `routes/__init__.py`. SHOP_ITEMS dict matches mini-program `points-shop.js`. Invite code format `BRO{user_id:06d}`. Both inviter & invitee get 50 points on bind.
- [ ] **F.3** Backend tests: `test_exchange.py` (4 tests) + `test_invite.py` (4 tests). Run pytest. Commit F.1+F.2+F.3.
- [ ] **F.4** Mini-program: `utils/api.js` add `getShopItems`, `redeem`, `getExchangeHistory`, `bindInvite`, `getInvitees`. `pages/points-shop/points-shop.js` `redeem()` calls `api.redeem(itemId)`. `pages/invite/invite.js` `onShow` fetches invitees list. `app.js` `onLaunch` reads `options.query.invite` and auto-binds after login. Commit.

**Acceptance:** `pytest tests/test_exchange.py tests/test_invite.py` 8 passed; manual: in points-shop with 100 points → redeem 50-cost item → backend records, points becomes 50. Two users — A's code `BRO000001` shared to B → B opens via `/pages/index/index?invite=BRO000001` → both get +50.

---

### Batch G — Leaderboard Time Dimension + Lexicon Corpus + Notification Backend (items #13, #14, #16)
- [ ] **G.1** Leaderboard: `routes/leaderboard.py` add `period` param (all/week/month) — filter UserProgress by `answered_at >= cutoff`. Update `test_leaderboard.py` with 2 new tests (period=week, period=month). `pages/leaderboard/leaderboard.{js,wxml}` add period tabs. Commit.
- [ ] **G.2** Lexicon: add `LexiconWord` model (id, word, definition, example, subject, created_at). Migration adds table. Create `routes/lexicon.py` with `GET /api/lexicon?subject=`. Seed 20 words across subjects in `backend/seeds/lexicon_seed.json`, extend `seed_questions.py` (or new `seed_lexicon.py`) to load it. `pages/licitong/licitong.js` fetch from API instead of hardcoded; pass subject from `selectedSubject`. Tests for lexicon endpoint. Commit.
- [ ] **G.3** Notification: add `Notification` model (id, user_id, type, title, content, read, created_at). Migration. `routes/notification.py` with `GET /api/notifications`, `POST /api/notifications/:id/read`, `POST /api/notifications/read-all`. `pages/notifications/notifications.js` fetch from backend, fallback to local hardcoded if not logged in. Tests. Commit.

**Acceptance:** All 3 new endpoint groups have passing tests; manual: leaderboard week tab filters; licitong shows seeded words; notifications page shows DB rows for logged-in user.

---

### Batch H — Study Room Cloud Sync (item #15)
- [ ] **H.1** Backend: extend `User` model with `study_seconds_today` and `study_date` (or simpler: create `StudySession` model with user_id, started_at, ended_at, seconds). New route `routes/study.py` with `POST /api/study/session` (body: seconds) and `GET /api/study/today`. Migration. Tests.
- [ ] **H.2** Mini-program: `utils/api.js` add `submitStudySession`, `getStudyToday`. `pages/studyroom/studyroom.js` on `stop()` — if logged in, POST session; on `onLoad` — if logged in, fetch today total from backend instead of local. Commit.

**Acceptance:** `pytest tests/test_study.py` passed; manual: start timer 1 minute → stop → re-open page → today total reflects 1 minute.

---

### Batch I — OCR & Web-Admin Validation (items #6, #7)
- [ ] **I.1** Verify `/api/import/upload` end-to-end: create a small text file with one question, POST as multipart; expect 200 with `parsed_questions` count. If OpenAI key not configured, fallback `_fallback_parse` should still extract pattern-matched questions. Document findings in `docs/ocr-import-status.md`. Add 1 smoke test `test_import_upload.py` that uses test client with FileStorage. Commit.
- [ ] **I.2** Verify web-admin can connect to local backend: check `web-admin/src/services/api.js` for `apiBase` URL, ensure CORS allowed, document any fixes needed. If trivial, fix; if needs npm/build chain validation, document as "verified config, full e2e needs npm install + start". Commit.

**Acceptance:** Import endpoint accepts plain-text and returns at least the fallback regex-parsed list. web-admin api.js points to correct base URL.

---

## Final Verification

After all batches:
- [ ] **V.1** Stop any running backend; run `pytest -v` → expect ≥20 tests passing
- [ ] **V.2** Start backend, end-to-end curl smoke for all new endpoints: `/api/exchange/items`, `/api/exchange` (with auth), `/api/invite/bind`, `/api/leaderboard?period=week`, `/api/lexicon?subject=数学`, `/api/notifications`, `/api/study/today`
- [ ] **V.3** Git log review — confirm one commit per batch task, push to origin

---

## Self-Review

**Spec coverage:** All 18 non-blocked items mapped to batches A–I.
**Placeholders:** Roadmap intentionally light on inline code; full code is delivered per-task in subagent prompts (no in-plan placeholder, only per-subagent specifics).
**Type consistency:** All new API method names match between backend route paths and mini-program `api.js`. SHOP_ITEMS dict is shared concept between `backend/routes/exchange.py` and `wechat-miniapp/pages/points-shop/points-shop.js` (controller must pass same item list to both).

---

## Execution Mode

**Subagent-Driven.** Controller (me) dispatches one subagent per batch (or sub-task within batch), each with complete inline code. I review reports between batches and run pytest myself for final verification.
