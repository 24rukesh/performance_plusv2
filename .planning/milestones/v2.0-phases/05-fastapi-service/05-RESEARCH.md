# Phase 5: FastAPI Service - Research

**Researched:** 2026-06-01
**Domain:** FastAPI + psycopg2 + multi-target Dockerfile + API key auth
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `POST /api/analyze` accepts two separate arrays: `web_sessions[]` and `crm_records[]`. Server merges on `session_id` + `campaign_id` using existing `data.py` logic.
- **D-02:** Both arrays use the same column names as the existing CSV schema — no renaming.
- **D-03:** Response shape is the existing `AnalysisResult` model directly — no wrapper envelope.
- **D-04:** FastAPI code lives in an `api/` package at the project root: `api/__init__.py`, `api/main.py`, `api/models.py`, `api/db.py`. Imports `llm.py` and `data.py` from the parent directory.
- **D-05:** Single `Dockerfile` with two build targets: `streamlit` target and `api` target. `compose.yaml` references both.
- **D-06:** `POST /api/webhook/crm` accepts a single CRM record, returns 202 immediately.
- **D-07:** Webhook payload stored in `pending_sessions` table for deferred analysis.
- **D-08:** Postgres service uses `postgres:16-alpine`, internal-only, named volume.
- **D-09:** psycopg2 + raw parameterized SQL only. No ORM. `DATABASE_URL` env var.
- **D-10:** `analysis_results` table: `id (serial PK), campaign_id (text), run_id (UUID), analyzed_at (timestamptz), result_json (JSONB)`.
- **D-11:** `pending_sessions` table: `id (serial PK), campaign_id (text), session_id (text), lead_status (text), projected_value (numeric), sales_notes (text), received_at (timestamptz)`.
- **D-12:** Auth FastAPI dependency checks `X-API-Key` header vs `API_KEY` env var. Returns 401 if missing or mismatched. Applied to all endpoints except `/api/health`.

### Claude's Discretion

None explicitly stated — all implementation details are locked via D-01 through D-12.

### Deferred Ideas (OUT OF SCOPE)

- Batch processing of `pending_sessions` — storing only, no batch analysis in Phase 5.
- Rate limiting per API key — single shared API key for v2.0.
- Async FastAPI + asyncpg — psycopg2 sync is the Phase 5 choice.
- Caddy routing for `/api` — deferred to Phase 8.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | Authorized client can POST /api/analyze with JSON payload and receive structured gpt-4o budget action recommendations (X-API-Key header required) | FastAPI `def` endpoint + APIKeyHeader dependency + existing `run_analysis()` call |
| API-02 | Analysis results persisted in Postgres keyed by campaign ID and timestamp | psycopg2 parameterized INSERT into `analysis_results` table; `Json` adapter for JSONB |
| API-03 | Authorized client can POST /api/webhook/crm with normalized CRM lead payload to ingest sessions (X-API-Key header required) | FastAPI 202 response + psycopg2 INSERT into `pending_sessions` |
| API-04 | Authorized client can GET /api/campaigns/{campaign_id}/actions to retrieve latest persisted analysis result (X-API-Key header required) | psycopg2 SELECT with ORDER BY analyzed_at DESC LIMIT 1 + JSONB read |
| API-05 | Any client can GET /api/health and receive 200 with service status and version (no auth) | Plain FastAPI endpoint, no dependency |

</phase_requirements>

---

## Summary

Phase 5 builds a FastAPI service on top of the existing `llm.py` and `data.py` logic. The intelligence layer (`run_analysis()`) is fully operational — Phase 5's work is a thin HTTP wrapper: expose it via five endpoints, add API key authentication via a FastAPI dependency, and wire Postgres persistence via psycopg2 raw SQL.

The most important architectural decision is already locked: use `def` (synchronous) endpoints, not `async def`. The existing `run_analysis()` → `_call_llm()` chain is synchronous and wraps a blocking I/O call (OpenAI SDK). FastAPI automatically runs `def` endpoints in a thread pool executor — this is the correct pattern for blocking I/O without event loop danger.

The second critical insight is the Python import path. The `api/` package sits at the project root and must import `llm` and `data` from the parent. Because uvicorn is launched from the project root (`uvicorn api.main:app --host 0.0.0.0 --port 8000`), the project root is already on `sys.path`. Direct imports (`import llm`, `from data import compute_campaign_agg`) work without any `sys.path` manipulation.

**Primary recommendation:** Build the `api/` package as a thin orchestration layer — never duplicate logic from `llm.py` or `data.py`. All five endpoints together should be under 150 lines of application code.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| API key authentication | API / Backend | — | Server-side header check; never in client code |
| Request body validation | API / Backend | — | FastAPI/Pydantic validates at the boundary before any logic runs |
| CSV merge + aggregation | API / Backend | — | `data.py` runs server-side; not browser-visible data |
| gpt-4o LLM call | API / Backend | — | `llm.py` called by endpoint; OpenAI SDK is sync, threadpool-safe |
| Result persistence (analysis_results) | Database / Storage | API / Backend | psycopg2 INSERT after successful LLM call; DB owns durability |
| Result retrieval | Database / Storage | API / Backend | psycopg2 SELECT; DB owns query; API shapes response |
| Webhook ingestion (pending_sessions) | Database / Storage | API / Backend | Immediate INSERT, 202 return; DB owns the queue |
| Container orchestration | CDN / Static | — | Docker compose adds `fastapi` + `postgres` services |
| TLS termination / routing | CDN / Static | — | Phase 8 concern — Caddy not touched in Phase 5 |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | **>=0.115,<1.0** | HTTP framework, routing, Pydantic integration, OpenAPI docs | Current stable series; 0.136.3 latest as of 2026-06-01. Industry standard for Python APIs with Pydantic v2. [VERIFIED: PyPI 2026-06-01] |
| uvicorn[standard] | **>=0.29,<1.0** | ASGI server to run FastAPI | Official FastAPI deployment server. `[standard]` extra adds watchfiles + httptools for production throughput. 0.48.0 latest. [VERIFIED: PyPI 2026-06-01] |
| psycopg2-binary | **>=2.9,<3.0** | PostgreSQL adapter, raw parameterized SQL | Binary distribution — no libpq-dev compile required in Docker slim image. 2.9.12 latest. [VERIFIED: PyPI 2026-06-01] |
| httpx | **>=0.27,<1.0** | ASGI test client for pytest | `httpx.AsyncClient(app=app)` is the recommended FastAPI test client. Already in venv (0.28.1). [VERIFIED: local venv] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | >=1.0 | Load `.env` locally | Already in `pyproject.toml`; `DATABASE_URL` + `API_KEY` added to `.env.example` |
| pytest | >=8 | Test framework | Already in dev deps (9.0.3 installed) |
| pytest-asyncio | >=0.23 | Async test support | Only if any endpoint tests use `async def`; with sync `def` endpoints, not strictly required |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg2-binary | asyncpg | asyncpg is faster and async-native but requires async endpoints and async context managers — deferred by D-09 |
| `def` endpoints | `async def` + `run_in_executor` | Would require wrapping `run_analysis()` in `asyncio.get_event_loop().run_in_executor()` — adds complexity for no Phase 5 benefit |
| Raw psycopg2 SQL | SQLAlchemy ORM | ORM adds migration tooling (Alembic) and query building — out of scope per D-09 |
| `httpx.TestClient` | `requests` | httpx is already installed and natively supports ASGI apps without a running server |

**Installation (new deps only — add to existing `pyproject.toml`):**
```bash
uv add "fastapi>=0.115,<1.0" "uvicorn[standard]>=0.29,<1.0" "psycopg2-binary>=2.9,<3.0"
uv add --dev "httpx>=0.27,<1.0"
```

**Note:** httpx is already installed (0.28.1). `uv add --dev` will simply update `pyproject.toml` if needed.

---

## Architecture Patterns

### System Architecture Diagram

```
External Client (n8n / CRM / curl)
        |
        | HTTP request (X-API-Key header)
        v
FastAPI app (api/main.py, port 8000)
        |
        +-- Auth dependency (api/main.py: verify_api_key)
        |       |-- PASS: continue to endpoint handler
        |       |-- FAIL: return 401 immediately
        |
        +-- POST /api/analyze
        |       |
        |       +-- Pydantic validates AnalyzeRequest body
        |       +-- pd.DataFrame(web_sessions) + pd.DataFrame(crm_records)
        |       +-- pd.merge(inner, validate="m:1") -> raises 422 on dup session_id
        |       +-- compute_campaign_agg(merged_df)          [data.py]
        |       +-- run_analysis(campaign_agg)               [llm.py -> OpenAI gpt-4o]
        |       +-- db.insert_analysis_result(campaign_id, run_id, result_json)
        |       +-- return AnalysisResult (JSON 200)
        |
        +-- GET /api/campaigns/{campaign_id}/actions
        |       |
        |       +-- db.get_latest_result(campaign_id)
        |       +-- return AnalysisResult JSON (200) or 404
        |
        +-- POST /api/webhook/crm
        |       |
        |       +-- Pydantic validates CrmWebhookRecord body
        |       +-- db.insert_pending_session(record)
        |       +-- return {"status": "accepted"} (202)
        |
        +-- GET /api/health (no auth)
                |
                +-- return {"status":"ok","version":"2.0.0","service":"performance-plus-api"} (200)
        |
        v
PostgreSQL (postgres:16-alpine, internal network)
        |
        +-- analysis_results table (keyed by campaign_id + run_id)
        +-- pending_sessions table (webhook queue)
```

### Recommended Project Structure

```
performance_plus/         # project root — uvicorn launched from here
├── api/
│   ├── __init__.py       # empty — marks as package
│   ├── main.py           # FastAPI app instance, all endpoint definitions, lifespan
│   ├── models.py         # AnalyzeRequest, CrmWebhookRecord (request bodies only)
│   └── db.py             # get_conn(), init_db(), insert_analysis_result(),
│                         #   get_latest_result(), insert_pending_session()
├── llm.py                # EXISTING — CampaignAction, AnalysisResult, run_analysis()
├── data.py               # EXISTING — compute_campaign_agg(), pd.merge
├── app.py                # EXISTING — Streamlit frontend (untouched)
├── Dockerfile            # REWRITTEN — adds api target alongside streamlit target
├── compose.yaml          # MODIFIED — adds fastapi + postgres services
├── pyproject.toml        # MODIFIED — adds fastapi, uvicorn, psycopg2-binary
├── .env.example          # MODIFIED — adds API_KEY, DATABASE_URL
└── tests/
    ├── test_api.py       # NEW — httpx TestClient tests for all 5 endpoints
    ├── test_db.py        # NEW — psycopg2 unit tests (mocked connection)
    └── ... (existing tests unchanged)
```

### Pattern 1: API Key Authentication Dependency

**What:** FastAPI Security dependency using `APIKeyHeader` that reads `X-API-Key` from headers and compares to `API_KEY` env var.
**When to use:** Apply to every protected endpoint via `Depends(verify_api_key)`.

```python
# Source: Context7 /fastapi/fastapi — security/APIKeyHeader pattern
import os
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    expected = os.environ.get("API_KEY")
    if not expected or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
```

**Key detail:** `auto_error=False` suppresses FastAPI's default 403 so we can raise 401 ourselves (per D-12). [VERIFIED: Context7 /fastapi/fastapi]

### Pattern 2: Sync Endpoint (Correct for Blocking I/O)

**What:** `def` (not `async def`) endpoint handler. FastAPI runs sync endpoints in a thread pool executor automatically — safe for blocking calls like psycopg2 and the OpenAI SDK.
**When to use:** Any endpoint that calls `run_analysis()` or psycopg2.

```python
# Source: Context7 /fastapi/fastapi — async.md "Use def for synchronous libraries"
@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(
    body: AnalyzeRequest,
    _: None = Depends(verify_api_key),
) -> AnalysisResult:
    # Runs in threadpool — blocking calls are safe here
    web_df = pd.DataFrame([s.model_dump() for s in body.web_sessions])
    crm_df = pd.DataFrame([c.model_dump() for c in body.crm_records])
    try:
        merged_df = pd.merge(web_df, crm_df, on=["session_id", "campaign_id"],
                             how="inner", validate="m:1")
    except pd.errors.MergeError as e:
        raise HTTPException(status_code=422, detail=f"Duplicate session_id in crm_records: {e}")
    campaign_agg = compute_campaign_agg(merged_df)
    result = run_analysis(campaign_agg)
    run_id = str(uuid.uuid4())
    for campaign in result.campaigns:
        insert_analysis_result(campaign.campaign_id, run_id, result)
    return result
```

[VERIFIED: Context7 /fastapi/fastapi]

### Pattern 3: psycopg2 Raw SQL with JSONB

**What:** Direct psycopg2 connection from `DATABASE_URL`, parameterized INSERT using `%s` placeholders, `Json()` adapter for JSONB columns.
**When to use:** All database operations in `api/db.py`.

```python
# Source: Context7 /psycopg/psycopg2 — usage.rst + extras.rst
import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def insert_analysis_result(campaign_id: str, run_id: str, result) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analysis_results
                    (campaign_id, run_id, analyzed_at, result_json)
                VALUES (%s, %s, NOW(), %s)
                """,
                (campaign_id, run_id, Json(result.model_dump())),
            )
        conn.commit()

def get_latest_result(campaign_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT result_json FROM analysis_results
                WHERE campaign_id = %s
                ORDER BY analyzed_at DESC
                LIMIT 1
                """,
                (campaign_id,),
            )
            row = cur.fetchone()
    return row[0] if row else None
```

**Key detail:** psycopg2 `with conn:` is a transaction context manager (auto-commits on success, rolls back on exception). It does NOT close the connection — `conn.close()` must still be called or connections will leak. For Phase 5's low concurrency this is acceptable; `get_conn()` creates a fresh connection per call. [VERIFIED: Context7 /psycopg/psycopg2]

### Pattern 4: Database Schema Initialization (lifespan)

**What:** FastAPI `lifespan` event runs DDL CREATE TABLE IF NOT EXISTS on startup so the schema is always present before the first request.
**When to use:** `api/main.py` lifespan function.

```python
# Source: Context7 /fastapi/fastapi — advanced/events.md
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # creates tables if not exist
    yield
    # no cleanup needed for psycopg2 per-request connections

app = FastAPI(lifespan=lifespan)
```

[VERIFIED: Context7 /fastapi/fastapi]

### Pattern 5: 202 Accepted Response

**What:** Return HTTP 202 for webhook ingestion — acknowledges receipt without implying processing.
**When to use:** `POST /api/webhook/crm`.

```python
# Source: Context7 /fastapi/fastapi — response-status-code.md
from fastapi import Response

@app.post("/api/webhook/crm", status_code=202)
def webhook_crm(
    record: CrmWebhookRecord,
    _: None = Depends(verify_api_key),
):
    insert_pending_session(record)
    return {"status": "accepted"}
```

[VERIFIED: Context7 /fastapi/fastapi]

### Pattern 6: Multi-Target Dockerfile

**What:** Single Dockerfile with a shared `builder` stage and two `FROM builder` runtime stages — `streamlit` and `api`.
**When to use:** Rewrite existing `Dockerfile` to add the `api` target.

```dockerfile
# syntax=docker/dockerfile:1.7

# ---- builder stage (shared) ----
FROM python:3.11-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---- streamlit runtime ----
FROM python:3.11-slim-bookworm AS streamlit
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ---- api runtime ----
FROM python:3.11-slim-bookworm AS api
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key detail:** Both runtime stages share the same `builder` layer — deps are only installed once. Docker layer cache is preserved because both targets descend from the same builder. [ASSUMED — based on standard Docker multi-stage pattern; verified functionally against existing Dockerfile structure]

### Pattern 7: compose.yaml Addition

**What:** Add `fastapi` and `postgres` services to `compose.yaml`. No changes to `app` or `caddy` services.
**When to use:** Phase 5 compose.yaml modification.

```yaml
services:
  app:
    build:
      context: .
      target: streamlit   # explicit target now required
    # ... rest unchanged

  fastapi:
    build:
      context: .
      target: api
    restart: unless-stopped
    env_file: .env
    networks:
      - internal
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: performance_plus
      POSTGRES_USER: ppuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal
    # No ports: exposed — internal only per D-08

volumes:
  postgres_data:
  # ... existing caddy volumes
```

**Key detail:** The existing `app` service build directive must be updated from `build: .` to `build: { context: ., target: streamlit }` once the Dockerfile has multiple targets. Without specifying `target`, Docker builds the last stage by default — which after the rewrite would be `api`, not `streamlit`. [VERIFIED: Docker multi-stage docs — last stage is default target]

### Anti-Patterns to Avoid

- **`async def` with blocking calls:** Using `async def analyze(...)` and calling `run_analysis()` directly would block the event loop. Use `def` for all endpoints that call `run_analysis()` or psycopg2. [VERIFIED: Context7 /fastapi/fastapi async.md]
- **Redefining `AnalysisResult` in `api/models.py`:** Import from `llm.py` directly. Redefining creates schema drift if `llm.py` changes. [CITED: 05-AI-SPEC.md section 4b]
- **`response_format={"type":"json_object"}` in any new LLM call:** JSON mode only. Always use existing `run_analysis()` path. [CITED: CLAUDE.md "What NOT to Use"]
- **`pd.merge(how="outer")` for the two-array merge:** Produces NaN rows that confuse gpt-4o. Use `how="inner"` with `validate="m:1"`. [CITED: CLAUDE.md, data.py existing pattern]
- **Not specifying `build.target` in compose.yaml for `app` service:** After multi-stage Dockerfile rewrite, the default built target shifts to the last stage (`api`). The `app` service must explicitly specify `target: streamlit`. [ASSUMED — derived from Docker docs behavior]
- **Using `conn` context manager (`with conn:`) as a connection closer:** `with conn:` manages the transaction (commit/rollback) only — it does NOT close the connection. Call `conn.close()` explicitly or connection count will grow. For Phase 5 low-volume usage this is safe with `get_conn()` per-call approach, but worth documenting. [VERIFIED: Context7 /psycopg/psycopg2]
- **Hardcoding `POSTGRES_PASSWORD` in `compose.yaml`:** Pass via `.env` and reference as `${POSTGRES_PASSWORD}`. [CITED: CLAUDE.md "What NOT to Use" section — API key pattern]
- **Missing `init_db()` guard — CREATE TABLE without IF NOT EXISTS:** Each restart will fail if tables already exist. Always use `CREATE TABLE IF NOT EXISTS`. [ASSUMED]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request body validation | Custom type-checking code | FastAPI + Pydantic v2 (already in stack) | Pydantic validates at boundary, generates OpenAPI schema, raises 422 with structured errors automatically |
| API key header extraction | Manual `request.headers.get(...)` in every endpoint | `fastapi.security.APIKeyHeader` + `Security()` | Appears in OpenAPI docs as a security scheme; auto_error control; consistent across endpoints |
| UUID generation | Custom ID schemes | `import uuid; str(uuid.uuid4())` | stdlib, zero deps |
| JSONB serialization | `json.dumps()` + manual casting | `psycopg2.extras.Json()` adapter | Handles Python dict → JSONB without manual escaping; psycopg2 auto-registers JSONB deserialization from Postgres 9.2+ |
| Schema migration / DDL management | Per-request CREATE TABLE | `CREATE TABLE IF NOT EXISTS` in `init_db()` called at lifespan startup | Idempotent, runs once, no migration tooling needed for 2-table Phase 5 scope |
| API contract tests | Manual HTTP requests | `httpx.TestClient(app)` | No running server needed; ASGI transport; already installed (0.28.1) |

**Key insight:** FastAPI + Pydantic v2 turns request validation into zero-code infrastructure. Never reimplement what the framework provides for free.

---

## Common Pitfalls

### Pitfall 1: `app` Service Builds Wrong Target After Dockerfile Rewrite

**What goes wrong:** After adding the `api` stage to `Dockerfile`, running `docker compose up` rebuilds the `app` service using the `api` stage (the last stage in the file) instead of `streamlit`. The Streamlit container silently starts uvicorn and the service fails health checks.

**Why it happens:** Docker multi-stage build defaults to the last stage when no `target` is specified. The existing `compose.yaml` has `build: .` with no target.

**How to avoid:** When rewriting `Dockerfile` to add the `api` target, simultaneously update `compose.yaml` `app` service to `build: { context: ., target: streamlit }`.

**Warning signs:** `docker compose ps` shows `app` service restarting; `docker compose logs app` shows uvicorn startup instead of Streamlit startup.

### Pitfall 2: `async def` Endpoint Blocks Event Loop

**What goes wrong:** Declaring `async def analyze(...)` and calling `run_analysis()` (which calls OpenAI SDK synchronously) blocks the ASGI event loop for the 2–6 second gpt-4o round-trip. Under concurrent load, all other requests queue behind this one blocked coroutine.

**Why it happens:** FastAPI does not automatically offload `async def` endpoints to a thread pool — only `def` endpoints get that treatment.

**How to avoid:** Use `def` (not `async def`) for any endpoint that calls `run_analysis()` or any psycopg2 function. [VERIFIED: Context7 /fastapi/fastapi async.md]

**Warning signs:** API health check endpoint (`/api/health`) becomes slow when `/api/analyze` is in flight; concurrent requests timeout.

### Pitfall 3: psycopg2 Connection Leak

**What goes wrong:** Connections opened with `get_conn()` are not explicitly closed after use, exhausting the Postgres `max_connections` (default 100) after many requests.

**Why it happens:** `with conn:` (transaction context manager) does NOT close the connection — it only commits or rolls back. The Python GC eventually closes connections but not deterministically.

**How to avoid:** Always close connections explicitly. Use `try/finally` or a context manager wrapper:

```python
conn = get_conn()
try:
    with conn:
        with conn.cursor() as cur:
            cur.execute(...)
finally:
    conn.close()
```

Or use `psycopg2.pool.ThreadedConnectionPool` for a shared pool (see Phase 5 scope — per-call connections are fine for demo volume).

**Warning signs:** `FATAL: remaining connection slots are reserved for non-replication superuser` error from Postgres after sustained load.

### Pitfall 4: Import Fails Because `api/` Package Can't Find `llm.py`

**What goes wrong:** `from llm import run_analysis, AnalysisResult` inside `api/main.py` raises `ModuleNotFoundError` when uvicorn is launched from a different working directory or when running tests without the project root on `sys.path`.

**Why it happens:** Python resolves bare module names (`import llm`) relative to `sys.path`. The project root must be on `sys.path`.

**How to avoid:** Always launch uvicorn from the project root: `uvicorn api.main:app ...`. The Dockerfile `WORKDIR /app` + `CMD ["uvicorn", "api.main:app", ...]` guarantees this. For tests, use pytest's `conftest.py` to add the project root to sys.path, or run via `uv run pytest` from the project root (uv sets the venv root correctly). [VERIFIED: tested locally — `import llm` works from project root]

**Warning signs:** `ModuleNotFoundError: No module named 'llm'` on startup or in test runs.

### Pitfall 5: Duplicate `session_id` in `crm_records` Raises 500 Instead of 422

**What goes wrong:** `pd.merge(validate="m:1")` raises `pd.errors.MergeError` when `crm_records` contains duplicate `session_id` values. If uncaught, FastAPI returns a 500 Internal Server Error.

**Why it happens:** FastAPI does not know how to map a pandas MergeError to a 422. Pydantic validation only covers the request body shape, not the merge constraint.

**How to avoid:** Wrap the `pd.merge` call in a `try/except pd.errors.MergeError` block and raise `HTTPException(status_code=422, detail="Duplicate session_id in crm_records")`.

**Warning signs:** 500 responses on valid-shaped but semantically invalid payloads; merge error in server logs.

### Pitfall 6: JSONB Column Returns String Instead of Dict on Read

**What goes wrong:** `cur.fetchone()` returns the `result_json` column as a Python string (`'{"executive_summary": ...}'`) instead of a dict, breaking `AnalysisResult.model_validate(row[0])`.

**Why it happens:** psycopg2 older than 2.5.4 doesn't auto-register the JSONB typecaster. On versions >=2.5.4 (current: 2.9.12) this is auto-handled, but only if `psycopg2.extras` is imported before use. [VERIFIED: Context7 /psycopg/psycopg2 — faq.rst]

**How to avoid:** Import `psycopg2.extras` in `db.py` (already needed for `Json` adapter). On psycopg2 2.9.x, JSONB columns are automatically deserialized to Python dicts.

**Warning signs:** `AttributeError: 'str' object has no attribute 'get'` when passing `row[0]` to `AnalysisResult.model_validate()`.

### Pitfall 7: MergeError on Empty Arrays After Inner Join

**What goes wrong:** `POST /api/analyze` receives valid `web_sessions` and `crm_records` that share no `session_id` values. `pd.merge(how="inner")` returns an empty DataFrame. `compute_campaign_agg()` on an empty DataFrame returns an empty DataFrame. `run_analysis()` sends zero-row CSV to gpt-4o, which may return `insufficient_data` for all campaigns or fail with a refusal.

**Why it happens:** The inner join succeeds (no MergeError) but produces no matching rows.

**How to avoid:** Add an explicit empty-result guard after the merge:

```python
if merged_df.empty:
    raise HTTPException(
        status_code=422,
        detail="No session_id overlap between web_sessions and crm_records"
    )
```

**Warning signs:** gpt-4o returns `insufficient_data` on all campaigns or a refusal; no MergeError in logs but bad output.

---

## Code Examples

Verified patterns from official sources:

### Full `api/db.py` skeleton

```python
# Source: Context7 /psycopg/psycopg2 — usage.rst, extras.rst
import os
import psycopg2
import psycopg2.extras  # required for Json adapter + JSONB auto-deserialization
from psycopg2.extras import Json


def get_conn():
    """Open a new connection. Caller is responsible for close()."""
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db() -> None:
    """Create tables if they don't exist. Called at lifespan startup."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id          SERIAL PRIMARY KEY,
                        campaign_id TEXT NOT NULL,
                        run_id      UUID NOT NULL,
                        analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        result_json JSONB NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pending_sessions (
                        id              SERIAL PRIMARY KEY,
                        campaign_id     TEXT NOT NULL,
                        session_id      TEXT NOT NULL,
                        lead_status     TEXT,
                        projected_value NUMERIC,
                        sales_notes     TEXT,
                        received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
    finally:
        conn.close()


def insert_analysis_result(campaign_id: str, run_id: str, result) -> None:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analysis_results
                        (campaign_id, run_id, analyzed_at, result_json)
                    VALUES (%s, %s::uuid, NOW(), %s)
                    """,
                    (campaign_id, run_id, Json(result.model_dump())),
                )
    finally:
        conn.close()


def get_latest_result(campaign_id: str) -> dict | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT result_json FROM analysis_results
                WHERE campaign_id = %s
                ORDER BY analyzed_at DESC
                LIMIT 1
                """,
                (campaign_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def insert_pending_session(record) -> None:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pending_sessions
                        (campaign_id, session_id, lead_status, projected_value,
                         sales_notes, received_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        record.campaign_id,
                        record.session_id,
                        record.lead_status,
                        record.projected_value,
                        record.sales_notes,
                    ),
                )
    finally:
        conn.close()
```

### `api/models.py` — Request body models only

```python
# Source: 05-AI-SPEC.md section 4b — "request body only, not the LLM response schema"
from pydantic import BaseModel


class WebSession(BaseModel):
    session_id: str
    campaign_id: str
    clicks: int
    impressions: int
    cost_usd: float
    conversion_rate: float


class CrmRecord(BaseModel):
    session_id: str
    campaign_id: str
    lead_status: str
    projected_value: float
    sales_notes: str


class AnalyzeRequest(BaseModel):
    web_sessions: list[WebSession]
    crm_records: list[CrmRecord]


class CrmWebhookRecord(BaseModel):
    session_id: str
    campaign_id: str
    lead_status: str
    projected_value: float
    sales_notes: str
```

### httpx TestClient pattern for FastAPI endpoint tests

```python
# Source: FastAPI docs — testing with httpx; httpx 0.28.1 already installed
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_analyze_missing_auth():
    response = client.post("/api/analyze", json={"web_sessions": [], "crm_records": []})
    assert response.status_code == 401

def test_analyze_with_auth(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setattr("llm.client", None)
    response = client.post(
        "/api/analyze",
        headers={"X-API-Key": "test-key"},
        json={"web_sessions": [...], "crm_records": [...]},
    )
    assert response.status_code == 200
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` decorator | `lifespan` async context manager | FastAPI 0.95 (2023) | `on_event` deprecated; `lifespan` is the current pattern |
| `response_format={"type":"json_object"}` | `client.beta.chat.completions.parse(response_format=PydanticModel)` | OpenAI SDK 1.40 + gpt-4o-2024-08-06 | Structured Outputs enforce schema server-side; JSON mode only guarantees valid JSON |
| `pip install` + `requirements.txt` | `uv add` + `uv.lock` | 2024 (uv adoption) | Deterministic lockfile, 10-100x faster installs, Docker cache-friendly |
| `from starlette.testclient import TestClient` | `from fastapi.testclient import TestClient` | FastAPI 0.68+ | FastAPI re-exports the TestClient; use the FastAPI path for consistency |

**Deprecated/outdated:**
- `@app.on_event("startup")`: Works but deprecated since FastAPI 0.95. Use `lifespan` context manager instead.
- Pydantic v1: Not supported by OpenAI's `.parse()` helper; not in scope.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Multi-target Dockerfile uses single builder layer shared by both runtime stages — Docker layer cache preserved | Architecture Patterns Pattern 6 | If wrong, both stages rebuild deps independently, doubling build time. Functionally correct either way. |
| A2 | `CREATE TABLE IF NOT EXISTS` in `init_db()` is idempotent on Postgres 16 | Code Examples db.py | Standard SQL behavior since Postgres 9.1; virtually no risk |
| A3 | The `app` service in `compose.yaml` must explicitly specify `target: streamlit` after multi-stage Dockerfile rewrite, or Docker defaults to last stage | Pitfall 1, Architecture Patterns | HIGH risk if wrong — Streamlit container would run uvicorn instead. Standard Docker behavior but not tested in this codebase yet. |
| A4 | `fastapi.testclient.TestClient` from httpx (0.28.1) works for ASGI app testing without a running server | Code Examples | httpx 0.28.x is current; TestClient is stable API. Very low risk. |

**If this table is empty:** All claims were verified or cited — no user confirmation needed.
The 4 assumptions above are low-to-medium risk. A3 is the highest-risk assumption and should be the first thing verified during execution.

---

## Open Questions (RESOLVED)

1. **DATABASE_URL format for local dev vs Docker**
   - What we know: psycopg2 accepts standard PostgreSQL DSN: `postgresql://user:password@host:port/dbname`
   - What's unclear: On the VPS, the FastAPI container connects to `postgres` (Docker service hostname). Locally without Docker, developers would need a local Postgres instance or a docker-compose local run.
   - RESOLVED: `.env.example` documents both: `DATABASE_URL=postgresql://ppuser:password@postgres:5432/performance_plus` (Docker) and notes that local dev requires `docker compose up postgres` first. Tests that exercise DB mock psycopg2 at unit level; integration tests use `DATABASE_URL` env var.

2. **Test isolation for `analysis_results` and `pending_sessions` tables**
   - What we know: pytest tests that hit real Postgres need a test database and teardown.
   - What's unclear: Phase 5 scope (no CI) — should `test_db.py` mock psycopg2 or require a real DB?
   - RESOLVED: Unit tests mock psycopg2 with `unittest.mock.patch`. Integration tests (marked `@pytest.mark.integration`) use a real DB via `DATABASE_URL` env var. Confirmed in AI-SPEC eval section and 05-04-PLAN.md test design.

3. **`api/main.py` insert loop — one row per campaign vs one row per run**
   - What we know: D-10 says `analysis_results` stores one row per campaign per run. `POST /api/analyze` returns one `AnalysisResult` with multiple `CampaignAction` items.
   - What's unclear: Should the INSERT loop in the endpoint iterate over `result.campaigns` (one INSERT per `campaign_id`) or store the full `AnalysisResult` once with a sentinel `campaign_id`?
   - RESOLVED: Iterate over `result.campaigns` — one row per `campaign_id`, same `run_id`. This enables the `GET /api/campaigns/{campaign_id}/actions` query to use `WHERE campaign_id = $1` efficiently without JSON path filtering. Implemented in 05-03-PLAN.md Task 1.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 | FastAPI runtime | ✓ | 3.11 (uv-managed venv) | — |
| uv | Dep management + Docker | ✓ | 0.11.8 | — |
| fastapi | API framework | ✗ (not yet installed) | 0.136.3 on PyPI | None — must install |
| uvicorn[standard] | ASGI server | ✗ (not yet installed) | 0.48.0 on PyPI | None — must install |
| psycopg2-binary | PostgreSQL adapter | ✗ (not yet installed) | 2.9.12 on PyPI | None — must install |
| httpx | Test client (already installed) | ✓ | 0.28.1 | — |
| pytest | Test runner | ✓ | 9.0.3 | — |
| Docker | Container build + local Postgres | ✗ (not available locally) | — | Run tests with mocked DB; integration tests require `docker compose up postgres` |
| PostgreSQL | Result persistence | ✗ (not available locally) | — | Unit tests mock psycopg2; integration tests require Docker compose |

**Missing dependencies with no fallback:**
- `fastapi`, `uvicorn[standard]`, `psycopg2-binary` — must be added via `uv add` before any implementation. These are PyPI packages with no blocker.

**Missing dependencies with fallback:**
- Docker / PostgreSQL — not available on this dev machine. Unit tests must mock psycopg2. Integration tests require `docker compose up postgres` (full env). Does not block coding the API layer.

---

## Security Domain

> `security_enforcement: true` + `security_asvs_level: 1` in `.planning/config.json`.

### Applicable ASVS Categories (ASVS Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user accounts in Phase 5 |
| V3 Session Management | No | Stateless API; no sessions |
| V4 Access Control | Yes | API key dependency `verify_api_key` on protected endpoints; `/api/health` explicitly excluded |
| V5 Input Validation | Yes | FastAPI + Pydantic v2 validates all request bodies at the boundary; `validate="m:1"` on merge; empty input guard |
| V6 Cryptography | No | API key is a shared secret compared with `==`; no cryptographic operations needed at ASVS Level 1 |
| V7 Error Handling | Yes | Never return stack traces to clients; FastAPI default 422/500 handlers are safe; catch MergeError → 422, not 500 |
| V8 Data Protection | Low | Synthetic/mock data only for v2.0. No PII in CRM records. Flag for v3+ real CRM data. |

### Known Threat Patterns for FastAPI + psycopg2

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via unsanitized input | Tampering | psycopg2 parameterized queries (`%s` placeholders) — never use string interpolation in SQL |
| API key brute force | Elevation of Privilege | Not mitigated in Phase 5 (single-tenant demo). Rate limiting deferred. Accept for MVP. |
| OPENAI_API_KEY / API_KEY leakage via logs | Information Disclosure | Never log env var values. FastAPI default error handler does not include env vars in responses. |
| Oversized payload exhausting Postgres | Denial of Service | Pydantic model bounds; for v2.0 demo scale, not a practical threat. FastAPI default max body size applies. |
| Empty `sales_notes` triggering hallucinated LLM reasoning | Integrity | `validate="m:1"` on merge ensures no orphan rows; empty CRM notes are passed through; LLM may produce vague reasoning (documented failure mode in AI-SPEC). |

**Security note:** `X-API-Key` comparison uses Python `==` (string equality). This is susceptible to timing attacks in high-security environments. For Phase 5 single-tenant demo, acceptable. For v3+ multi-tenant: use `hmac.compare_digest()` instead. [ASSUMED — standard security guidance]

---

## Sources

### Primary (HIGH confidence)
- Context7 `/fastapi/fastapi` — APIKeyHeader, sync def endpoints, lifespan, response status codes, bigger-applications project structure, TestClient
- Context7 `/psycopg/psycopg2` — parameterized INSERT/SELECT, `Json` adapter for JSONB, connection pool, fetchone/fetchall, transaction context manager
- `./llm.py` (local codebase) — CampaignAction, AnalysisResult, run_analysis() signatures and behavior
- `./data.py` (local codebase) — compute_campaign_agg() signature, pd.merge pattern
- `./Dockerfile` (local codebase) — non-root user pattern, builder stage, uv sync pattern
- `./compose.yaml` (local codebase) — existing service structure
- `./pyproject.toml` (local codebase) — current deps, Python version
- `.planning/phases/05-fastapi-service/05-CONTEXT.md` — all locked decisions D-01 through D-12
- `.planning/phases/05-fastapi-service/05-AI-SPEC.md` — framework selection, async/sync guidance, Pydantic import strategy

### Secondary (MEDIUM confidence)
- PyPI registry — fastapi 0.136.3, uvicorn 0.48.0, psycopg2-binary 2.9.12, httpx 0.28.1 (all verified 2026-06-01)
- CLAUDE.md — stack constraints, Dockerfile patterns, uv usage conventions
- Local venv inspection — httpx 0.28.1, pydantic 2.13.4, pytest 9.0.3 confirmed installed

### Tertiary (LOW confidence — flagged)
- Docker multi-stage default-target behavior (A3) — standard documented behavior; not tested in this specific codebase

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — verified against PyPI registry 2026-06-01
- Architecture: HIGH — derived from existing codebase + Context7 verified patterns
- Pitfalls: HIGH — most derived from Context7 official docs + existing code analysis; A3 is the only LOW item
- Security: MEDIUM — ASVS Level 1 standard patterns; demo-scale threat model

**Research date:** 2026-06-01
**Valid until:** 2026-07-01 (FastAPI 0.115+ stable series; psycopg2-binary 2.9.x stable)
