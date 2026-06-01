---
phase: "06-waitlist-backend"
plan: "02"
subsystem: "api"
tags: ["waitlist", "cors", "endpoint", "tests", "fastapi"]
dependency_graph:
  requires: ["06-01"]
  provides: ["POST /api/waitlist endpoint", "CORS middleware", "waitlist contract tests"]
  affects: ["api/main.py", "tests/test_api.py"]
tech_stack:
  added: []
  patterns: ["CORSMiddleware wildcard registration", "public endpoint (no verify_api_key)", "DB-first then SMTP order (D-14)", "api.main.* patching for TestClient mocks"]
key_files:
  created: []
  modified:
    - path: "api/main.py"
      description: "Added CORSMiddleware, new imports, POST /api/waitlist endpoint (lines 8-13 imports, line 34 CORS, lines 76-83 endpoint)"
    - path: "tests/test_api.py"
      description: "Appended four contract tests for POST /api/waitlist (lines 408-457)"
decisions:
  - "D-05 honored: CORSMiddleware registered with allow_origins=['*'], no allow_credentials=True (FastAPI rejects wildcard+credentials)"
  - "D-06 honored: SMTP failures raise HTTPException(500) with 'SMTP error:' prefix — fail loudly, not silently"
  - "D-11 honored: waitlist_signup uses sync def, matching existing project convention"
  - "D-12 honored: no Depends(verify_api_key) on POST /api/waitlist — public endpoint, no auth gate"
  - "D-14 honored: insert_waitlist_email called before send_waitlist_notification — DB commit before email"
metrics:
  duration: "82s"
  completed_date: "2026-06-01"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 06 Plan 02: Waitlist Endpoint + CORS Summary

**One-liner:** Public POST /api/waitlist endpoint with CORSMiddleware wiring insert_waitlist_email and send_waitlist_notification, proven by four TestClient contract tests covering 200/422/409/500 paths.

## What Was Built

### Task 1: CORSMiddleware + POST /api/waitlist in api/main.py

Three additions to `api/main.py` (original 71 lines, now 84 lines):

**New imports (lines 8, 11-13):**
- `from fastapi.middleware.cors import CORSMiddleware`
- `insert_waitlist_email` added to `from api.db import ...` (alphabetical order maintained)
- `from api.email_utils import send_waitlist_notification`
- `WaitlistRequest` added to `from api.models import ...` (alphabetical order maintained)

**CORS middleware (line 34)** — inserted immediately after `app = FastAPI(...)` and before all route decorators:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

**Endpoint (lines 76-83)** — appended at file bottom:
- Sync `def` (project convention, D-11)
- No `Depends(verify_api_key)` (public endpoint, D-12)
- DB insert first, SMTP second (D-14 order)
- HTTPException 409 from `insert_waitlist_email` propagates uncaught
- SMTP exceptions wrapped as HTTPException 500 with `"SMTP error:"` prefix (D-06)

### Task 2: Four contract tests in tests/test_api.py

Appended under `# POST /api/waitlist — four behavioral contracts` section header (lines 408-457):

| Test | Contract | Assertion focus |
|------|----------|----------------|
| `test_waitlist_valid_email_returns_200` | WAIT-01, WAIT-02 | 200 + exact body + mock call args verified |
| `test_waitlist_invalid_email_returns_422` | Pydantic validation | 422 without touching DB or SMTP |
| `test_waitlist_duplicate_email_returns_409` | WAIT-02 duplicate guard | 409 + exact detail string propagated |
| `test_waitlist_smtp_failure_returns_500` | WAIT-03 owner notification | 500 + detail contains "SMTP error:" |

All four use the existing `_make_client(monkeypatch, db_overrides=...)` factory, patching at `api.main.*` binding level (Pitfall 5 compliance).

## Requirements Completed

| Requirement | Description | Proved by |
|-------------|-------------|-----------|
| WAIT-01 | Visitor receives confirmation message | `test_waitlist_valid_email_returns_200` — asserts `{"message": "You're on the waitlist! We'll be in touch."}` |
| WAIT-02 | Signup stored (duplicate rejected 409) | `test_waitlist_duplicate_email_returns_409` — asserts 409 with correct detail |
| WAIT-03 | Owner notified via SMTP (failure surfaces as 500) | `test_waitlist_smtp_failure_returns_500` — asserts 500 with "SMTP error:" |

## Decisions Honored

- **D-05:** `allow_origins=["*"]` without `allow_credentials=True` — FastAPI rejects wildcard + credentials combination
- **D-06:** SMTP failures wrapped as `HTTPException(500, detail=f"SMTP error: {exc}")` — fail loudly, not silently
- **D-11:** `def waitlist_signup(...)` is sync, matching all other route handlers in the file
- **D-12:** No `Depends(verify_api_key)` on the endpoint — public route, no auth gate required
- **D-14:** `insert_waitlist_email` called before `send_waitlist_notification` — DB commit before email ensures email only sent after storage is guaranteed

## Verification Results

```
uv run pytest tests/test_api.py -x -q -k waitlist
4 passed in 0.96s

uv run pytest tests/test_api.py -v
18 passed in 0.58s  (all 14 pre-existing Phase 5 tests still green)

CORS preflight smoke check: OK (access-control-allow-origin: *)
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — endpoint is fully wired to Plan 01 primitives with no placeholder values or hardcoded empty returns.

## VPS Deployment Note

Manual VPS deployment verification (Caddy WebSocket proxy, live Postgres, live SMTP) is deferred to Phase 8 per plan scope. The endpoint and tests are self-contained and ready for deployment.

## Self-Check: PASSED

- api/main.py exists and contains `@app.post("/api/waitlist"`: FOUND
- api/main.py contains `app.add_middleware(CORSMiddleware`: FOUND
- tests/test_api.py contains `def test_waitlist_`: FOUND (4 functions)
- Commit e40f7f2 (Task 1): FOUND
- Commit fe4089c (Task 2): FOUND
