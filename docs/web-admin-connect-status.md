# Web-Admin → Local Backend Connectivity Report

**Date:** 2026-06-11
**Investigated by:** Round 2 buildout, Batch I.2

## Configuration

- Backend listens on `http://127.0.0.1:5001`
- `backend/app.py` calls `CORS(app)` → all origins allowed by default
- `web-admin/src/services/api.js` API_BASE: previously `http://106.53.188.248/api`, **now patched to** `http://127.0.0.1:5001/api` (still honors `REACT_APP_API_URL` env override)

## Status

- [x] CORS configured on backend (`CORS(app)` in `backend/app.py:11`)
- [x] api.js base URL points to local backend (fixed in this batch)
- [x] Endpoints used by web-admin exist: `/import/upload`, `/import/batches`, `/import/batch/<id>/questions`, `/import/question/<id>/approve|reject` (all defined in `backend/routes/import.py`)

## Gaps / Notes

- api.js previously pointed to the old production host `106.53.188.248`. Fixed in-place; downstream deployments that depend on the prod URL should now set `REACT_APP_API_URL` explicitly.
- Full e2e test would require `cd web-admin && npm install && npm start` (not done as part of this batch — would need network + significant time).
- OCR path uses `_fallback_parse` regex when `OPENAI_API_KEY` is unset, so uploads work locally without external services.

## Recommendation

For local dev with web-admin:
1. `web-admin/src/services/api.js` already targets `http://127.0.0.1:5001/api`.
2. `cd web-admin && npm install && npm start`
3. Open `http://localhost:3000` in browser.
4. Ensure backend is running: `cd backend && python app.py`.
