---
phase: 05-fastapi-service
plan: "04"
subsystem: testing
tags: [fastapi, pytest, testclient, httpx, monkeypatch, contract-tests]

# Dependency graph
requires:
  - phase: 05-fastapi-service/05-01
    provides: api/models.py and api/db.py — AnalyzeRequest, CrmWebhookRecord, db functions
  - phase: 05-fastapi-service/05-02
    provides: Dockerfile multi-target + compose.yaml
  - phase: 05-fastapi-service/05-03
    provides: api/main.py with all 5 endpoints, auth gate, lifespan
provides:
  - "pytest TestClient contract tests for all 5 FastAPI endpoints (14 test functions)"
  - "Auth gate verification for POST /api/analyze, POST /api/webhook/crm, GET /api/campaigns/{id}/actions"
  - "Input validation tests (empty arrays, duplicate session_id, no session_id overlap)"
  - "DB persistence side-effect tests (insert_analysis_result call count, shared run_id UUID)"
  - "Zero-infrastructure test execution (no live Postgres, no live gpt-4o)"
affects: [05-fastapi-service, verify-phase]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_make_client(monkeypatch, db_overrides) helper pattern for FastAPI TestClient with monkeypatched deps"
    - "Patch api.main.{name} (not api.db.{name}) to override functions imported via 'from ... import'"
    - "DEMO_MODE=1 + llm.client=None forces fixture branch in llm.run_analysis"
    - "TestClient used as context manager (with _make_client(...) as client:) to trigger lifespan"

key-files:
  created:
    - tests/test_api.py
  modified: []

key-decisions:
  - "Happy path test also mocks insert_analysis_result (required since no Postgres in CI)"
  - "Patching api.main namespace (not api.db namespace) because api/main.py uses 'from api.db import ...'"
  - "Pre-existing test_deploy_config failure (3 Dockerfile stages vs expected 2) logged as deferred — out of scope"

patterns-established:
  - "_make_client pattern: set env vars via monkeypatch, then import app inside helper to capture patched state"
  - "All DB mock overrides passed as db_overrides dict to _make_client for consistency"

requirements-completed: [API-01, API-02, API-03, API-04, API-05]

# Metrics
duration: 3min
completed: 2026-06-01
---

# Phase 5 Plan 04: FastAPI Contract Tests Summary

**pytest TestClient suite with 14 tests covering auth gates, input validation, DB side-effects, and happy paths for all 5 endpoints — zero infrastructure required (no Postgres, no gpt-4o)**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-01T06:12:56Z
- **Completed:** 2026-06-01T06:15:16Z
- **Tasks:** 1
- **Files modified:** 1 (tests/test_api.py created)

## Accomplishments
- Created `tests/test_api.py` with 14 test functions covering all 5 API endpoints
- Verified auth gates on 3 endpoints (401 without X-API-Key, health endpoint open)
- Verified input validation: empty arrays, duplicate session_id (m:1 merge error), no session_id overlap
- Verified DB persistence: insert_analysis_result call count, shared UUID run_id, correct campaign_id set
- Verified webhook: insert_pending_session called with correct CrmWebhookRecord attributes
- Verified campaigns actions: 404 on None result, 200 + exact dict on result, get_latest_result called with campaign_id
- All 14 tests pass; no new regressions introduced

## Task Commits

1. **Task 1: Create tests/test_api.py** - `4b06bac` (feat)

**Plan metadata:** (created in this summary commit)

## Files Created/Modified
- `tests/test_api.py` - 14-function pytest TestClient contract test suite (404 lines)

## Decisions Made
- Happy path test (`test_analyze_happy_path_returns_200_with_analysis_result`) must also mock `insert_analysis_result` via db_overrides — the plan's sample helper only patches db_overrides when passed in, but the happy path test needs the mock to avoid a real DB call during the analyze loop. Added the mock as a Rule 1 auto-fix (bug: test would fail without it since no DATABASE_URL is set in CI).
- Followed plan guidance: patch `api.main.insert_analysis_result` (not `api.db.insert_analysis_result`) because `api/main.py` uses `from api.db import insert_analysis_result` which creates a local binding at import time.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Happy path test needed insert_analysis_result mock**
- **Found during:** Task 1 (initial test run)
- **Issue:** `test_analyze_happy_path_returns_200_with_analysis_result` called `_make_client(monkeypatch)` without db_overrides, so `insert_analysis_result` in the analyze loop hit the real `api.db.insert_analysis_result`, which called `get_conn()` → `psycopg2.connect(os.environ["DATABASE_URL"])` → `KeyError: 'DATABASE_URL'`
- **Fix:** Added `mock_insert = MagicMock()` and passed `db_overrides={"insert_analysis_result": mock_insert}` to `_make_client`
- **Files modified:** tests/test_api.py
- **Verification:** Re-ran `uv run pytest tests/test_api.py -v` — all 14 passed
- **Committed in:** 4b06bac (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential for test isolation. No scope creep.

## pytest Output Summary

```
============================= test session starts ==============================
collected 14 items

tests/test_api.py::test_health_returns_status_version_service PASSED
tests/test_api.py::test_health_no_auth_required PASSED
tests/test_api.py::test_analyze_missing_api_key_returns_401 PASSED
tests/test_api.py::test_analyze_wrong_api_key_returns_401 PASSED
tests/test_api.py::test_analyze_empty_arrays_returns_422 PASSED
tests/test_api.py::test_analyze_duplicate_crm_session_id_returns_422 PASSED
tests/test_api.py::test_analyze_no_session_overlap_returns_422 PASSED
tests/test_api.py::test_analyze_happy_path_returns_200_with_analysis_result PASSED
tests/test_api.py::test_analyze_persists_one_row_per_campaign_with_shared_run_id PASSED
tests/test_api.py::test_webhook_missing_api_key_returns_401 PASSED
tests/test_api.py::test_webhook_happy_path_returns_202_and_calls_insert_pending PASSED
tests/test_api.py::test_campaigns_actions_missing_api_key_returns_401 PASSED
tests/test_api.py::test_campaigns_actions_returns_404_when_no_results PASSED
tests/test_api.py::test_campaigns_actions_returns_latest_result_dict PASSED

============================== 14 passed in 0.94s ==============================
```

## Requirements Traceability

| Test Function | Requirement | Coverage |
|---|---|---|
| test_analyze_missing_api_key_returns_401 | API-01 | Auth gate |
| test_analyze_wrong_api_key_returns_401 | API-01 | Auth gate |
| test_analyze_empty_arrays_returns_422 | API-01 | Input validation |
| test_analyze_duplicate_crm_session_id_returns_422 | API-01 | Input validation |
| test_analyze_no_session_overlap_returns_422 | API-01 | Input validation |
| test_analyze_happy_path_returns_200_with_analysis_result | API-01 | Happy path + response shape |
| test_analyze_persists_one_row_per_campaign_with_shared_run_id | API-02 | DB persistence side-effects |
| test_webhook_missing_api_key_returns_401 | API-03 | Auth gate |
| test_webhook_happy_path_returns_202_and_calls_insert_pending | API-03 | Happy path + DB call |
| test_campaigns_actions_missing_api_key_returns_401 | API-04 | Auth gate |
| test_campaigns_actions_returns_404_when_no_results | API-04 | Not-found path |
| test_campaigns_actions_returns_latest_result_dict | API-04 | Happy path |
| test_health_returns_status_version_service | API-05 | Response contract |
| test_health_no_auth_required | API-05 | Auth-free access |

## Grep Gate Results

| Gate | Result |
|---|---|
| `grep -c "^def test_"` | 14 (>= 14 required) |
| `grep -c "requests.post\|requests.get"` | 0 (must be 0) |
| `grep -c "OPENAI_API_KEY"` | 0 (must be 0) |

## Known Stubs

None — all tests use real Pydantic validation + real endpoint logic with mocked infrastructure.

## Deferred Issues

**Pre-existing: `test_deploy_config.py::test_dockerfile_uses_python_3_11_slim_bookworm_in_both_stages`**
- Introduced by Plan 05-02 which added a third Dockerfile stage (`api` target)
- The test asserts exactly 2 `FROM python:3.11-slim-bookworm` lines; now there are 3
- Not introduced by this plan; logged to `deferred-items.md`
- Recommended fix: update test assertion to `count == 3` or `count >= 2`

## Issues Encountered

None beyond the auto-fixed deviation above.

## Next Phase Readiness

- All 5 API endpoints covered with contract tests — Phase 5 is now functionally complete
- `uv run pytest tests/test_api.py -v` exits 0 with 14 passing tests
- Phase is ready for `/gsd:verify-phase` verification
- One pre-existing failure in `test_deploy_config.py` should be addressed before verify-phase or explicitly accepted

---
*Phase: 05-fastapi-service*
*Completed: 2026-06-01*
