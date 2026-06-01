---
phase: 05-fastapi-service
plan: 01
subsystem: api
tags: [fastapi, psycopg2, pydantic, uvicorn, httpx, postgres]

# Dependency graph
requires:
  - phase: 04-deploy-config
    provides: pyproject.toml base dependency format, .env.example placeholder pattern
provides:
  - api/ Python package with Pydantic v2 request body models (WebSession, CrmRecord, AnalyzeRequest, CrmWebhookRecord)
  - api/db.py psycopg2 connection helper and 4 CRUD functions (get_conn, init_db, insert_analysis_result, get_latest_result, insert_pending_session)
  - fastapi, uvicorn[standard], psycopg2-binary runtime deps in pyproject.toml
  - httpx dev dep for FastAPI TestClient
  - API_KEY, DATABASE_URL, POSTGRES_PASSWORD placeholder keys in .env.example
affects: [05-02, 05-03, 05-04]

# Tech tracking
tech-stack:
  added:
    - fastapi==0.136.3
    - uvicorn==0.48.0
    - psycopg2-binary==2.9.12
    - httpx==0.28.1
    - uvloop==0.22.1 (uvicorn[standard] transitive)
    - watchfiles==1.2.0 (uvicorn[standard] transitive)
  patterns:
    - psycopg2 try/finally conn.close() pattern for connection lifecycle management
    - parameterized %s placeholders only — no f-string or .format() SQL construction
    - psycopg2.extras.Json adapter for JSONB column serialization
    - Pydantic v2 BaseModel without Field() for input models (Field reserved for LLM response schemas)
    - api/ package with empty __init__.py following tests/ convention

key-files:
  created:
    - api/__init__.py
    - api/models.py
    - api/db.py
  modified:
    - pyproject.toml
    - uv.lock
    - .env.example

key-decisions:
  - "psycopg2-binary chosen over asyncpg — sync driver matches FastAPI sync def endpoints and avoids asyncpg wheel complexity on Python 3.11-slim"
  - "api/models.py imports BaseModel only, no Field() — input models don't need LLM descriptions; Field reserved for response schemas in llm.py"
  - "try/finally conn.close() pattern in all 4 connection-opening functions — with conn: handles transactions but NOT connection close"
  - "AnalysisResult and CampaignAction NOT redefined in api/models.py — Plan 03 imports them directly from llm.py to prevent schema drift"

patterns-established:
  - "Pattern DB-1: get_conn() returns raw psycopg2 connection; caller must close via try/finally"
  - "Pattern DB-2: with conn: block handles commit/rollback; conn.close() in finally handles connection teardown"
  - "Pattern DB-3: Json(result.model_dump()) for JSONB columns; psycopg2.extras import required for auto-deserialization on read"
  - "Pattern MODEL-1: api/models.py contains only request body schemas; response schemas stay in llm.py"

requirements-completed: [API-02, API-03]

# Metrics
duration: 3min
completed: 2026-06-01
---

# Phase 5 Plan 01: FastAPI Package Scaffold Summary

**psycopg2 database layer + Pydantic v2 request models scaffolded as importable api/ package with parameterized SQL only (SQL injection gate: 0)**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-01T05:58:48Z
- **Completed:** 2026-06-01T06:02:00Z
- **Tasks:** 3
- **Files modified:** 6 (3 created, 3 modified)

## Accomplishments
- Added fastapi 0.136.3, uvicorn 0.48.0, psycopg2-binary 2.9.12 runtime deps and httpx 0.28.1 dev dep via uv; uv.lock regenerated
- Created api/ package with 4 Pydantic v2 BaseModel request body schemas matching frozen CSV column names
- Created api/db.py with 5 functions (get_conn, init_db, insert_analysis_result, get_latest_result, insert_pending_session) using parameterized SQL and try/finally connection close pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Add FastAPI/uvicorn/psycopg2/httpx deps and update .env.example** - `e9c7a40` (feat)
2. **Task 2: Create api/ package with __init__.py and api/models.py** - `709550f` (feat)
3. **Task 3: Create api/db.py with psycopg2 connection helper and 4 CRUD operations** - `aba9e19` (feat)

## Files Created/Modified
- `api/__init__.py` - Empty package marker (0 bytes)
- `api/models.py` - WebSession, CrmRecord, AnalyzeRequest, CrmWebhookRecord Pydantic v2 models
- `api/db.py` - psycopg2 connection helper + init_db (CREATE TABLE IF NOT EXISTS) + 4 CRUD functions
- `pyproject.toml` - Added fastapi>=0.115,<1.0, uvicorn[standard]>=0.29,<1.0, psycopg2-binary>=2.9,<3.0 + httpx>=0.27,<1.0 dev dep
- `uv.lock` - Regenerated (245 line changes; 5 new packages)
- `.env.example` - Appended API_KEY, DATABASE_URL, POSTGRES_PASSWORD placeholders

## Dependency Versions Installed

| Package | Version | Type |
|---------|---------|------|
| fastapi | 0.136.3 | runtime |
| uvicorn | 0.48.0 | runtime |
| psycopg2-binary | 2.9.12 | runtime |
| httpx | 0.28.1 | dev |
| uvloop | 0.22.1 | transitive (uvicorn[standard]) |
| watchfiles | 1.2.0 | transitive (uvicorn[standard]) |

## Verification Results

All final verification checks passed:

```
uv run python -c "from api.models import AnalyzeRequest, CrmWebhookRecord; from api.db import init_db, ..." -> all imports ok
grep fastapi>=0.115 pyproject.toml -> deps ok
grep API_KEY= .env.example -> env ok
grep "CREATE TABLE IF NOT EXISTS analysis_results" api/db.py -> tables ok
SQL injection grep gate (f-string/format INSERT/SELECT in non-comment lines) -> 0
```

## Decisions Made
- Used psycopg2-binary over asyncpg — sync driver matches FastAPI sync def endpoints per PATTERNS.md
- api/models.py uses BaseModel only (no Field descriptors) — input models don't need LLM schema descriptions
- try/finally conn.close() pattern in all connection-opening functions, not relying on with conn: for close
- AnalysisResult and CampaignAction intentionally NOT defined in api/models.py — api/main.py (Plan 03) imports from llm.py directly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required for this scaffold plan. DATABASE_URL and other secrets will be needed at runtime (documented in .env.example).

## Next Phase Readiness
- api/ package is fully importable: `from api.models import AnalyzeRequest; from api.db import init_db` both succeed
- Plan 03 (api/main.py) can immediately import from api.models and api.db
- Plan 04 (tests) can import from api.models for test fixtures
- DATABASE_URL environment variable must be set before init_db(), insert_*, get_* functions are called at runtime

---
*Phase: 05-fastapi-service*
*Completed: 2026-06-01*
