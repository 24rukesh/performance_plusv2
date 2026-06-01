# Phase 5: FastAPI Service - Pattern Map

**Mapped:** 2026-06-01
**Files analyzed:** 8 (4 new, 4 modified)
**Analogs found:** 8 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `api/__init__.py` | package marker | — | `tests/__init__.py` | role-match (empty package marker) |
| `api/main.py` | controller | request-response | `llm.py` (DEMO_MODE guard + OpenAI client init pattern) + `tests/test_llm.py` (endpoint structure) | partial (no existing HTTP controller; patterns assembled from llm.py + test fixtures) |
| `api/models.py` | model | request-response | `llm.py` lines 28–53 (Pydantic BaseModel + Field definitions) | exact (same Pydantic v2 BaseModel pattern) |
| `api/db.py` | service | CRUD | `data.py` lines 1–57 (function-per-operation, typed returns, raises on error) | role-match (same function decomposition; CRUD vs read-only) |
| `Dockerfile` | config | — | `Dockerfile` lines 1–51 (builder stage, non-root user, uv sync pattern) | exact (rewrite extends existing patterns) |
| `compose.yaml` | config | — | `compose.yaml` lines 1–32 (service definition, env_file, networks, volumes) | exact (additive modification) |
| `pyproject.toml` | config | — | `pyproject.toml` lines 1–23 (dependency declaration format) | exact (additive modification) |
| `.env.example` | config | — | `.env.example` lines 1–2 (KEY=value format, blank-value placeholder) | exact (additive modification) |

---

## Pattern Assignments

### `api/__init__.py` (package marker)

**Analog:** `tests/__init__.py` (empty file marking a Python package)

**Pattern:** Empty file. No imports, no content.

```python
# empty — marks api/ as a Python package
```

---

### `api/main.py` (controller, request-response)

**Analog (primary — Pydantic + DEMO_MODE guard):** `llm.py`
**Analog (secondary — test shape reveals expected call signatures):** `tests/test_llm.py`

**Imports pattern** — copy from `llm.py` lines 1–17, extend with FastAPI imports:

```python
# llm.py lines 1-17 — existing import style: stdlib first, then third-party, grouped
import json
import logging
import os
import time
from pathlib import Path
from typing import Literal

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import (...)
```

New `api/main.py` imports follow the same grouping convention:

```python
# stdlib
import os
import uuid
import logging
from contextlib import asynccontextmanager

# third-party
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

# local — direct imports from project root (uvicorn launched from /app)
from llm import AnalysisResult, run_analysis
from data import compute_campaign_agg
from api.models import AnalyzeRequest, CrmWebhookRecord
from api.db import get_latest_result, init_db, insert_analysis_result, insert_pending_session
```

**DEMO_MODE guard pattern** — copy from `llm.py` lines 99–100:

```python
# llm.py lines 99-100 — DEMO_MODE check: env var + None client guard
if os.environ.get("DEMO_MODE") == "1" and client is None:
    return _load_fixture()
```

The same `DEMO_MODE` env var is used in test fixtures (see `tests/test_llm.py` line 139: `monkeypatch.setenv("DEMO_MODE", "1")`). FastAPI tests use the same monkeypatch approach.

**Auth dependency pattern** — no existing analog in codebase; use RESEARCH.md Pattern 1 verbatim:

```python
# Source: 05-RESEARCH.md Architecture Patterns Pattern 1
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    expected = os.environ.get("API_KEY")
    if not expected or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
```

**Lifespan pattern** — no existing analog; use RESEARCH.md Pattern 4:

```python
# Source: 05-RESEARCH.md Architecture Patterns Pattern 4
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

**Core endpoint pattern (POST /api/analyze)** — merges `data.py` lines 26–32 merge pattern + `llm.py` lines 96–109 run_analysis pattern:

```python
# data.py lines 26-32 — merge pattern to replicate inside the endpoint
merged_df = pd.merge(
    web_df,
    crm_df,
    on=["session_id", "campaign_id"],
    how="inner",
    validate="m:1",
)

# llm.py lines 96-109 — run_analysis call pattern
result = run_analysis(campaign_agg)
```

Combined endpoint (sync def, not async def — see RESEARCH.md Pitfall 2):

```python
@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(
    body: AnalyzeRequest,
    _: None = Depends(verify_api_key),
) -> AnalysisResult:
    web_df = pd.DataFrame([s.model_dump() for s in body.web_sessions])
    crm_df = pd.DataFrame([c.model_dump() for c in body.crm_records])
    try:
        merged_df = pd.merge(
            web_df, crm_df,
            on=["session_id", "campaign_id"],
            how="inner",
            validate="m:1",
        )
    except pd.errors.MergeError as e:
        raise HTTPException(status_code=422, detail=f"Duplicate session_id in crm_records: {e}")
    if merged_df.empty:
        raise HTTPException(
            status_code=422,
            detail="No session_id overlap between web_sessions and crm_records",
        )
    campaign_agg = compute_campaign_agg(merged_df)
    result = run_analysis(campaign_agg)
    run_id = str(uuid.uuid4())
    for campaign in result.campaigns:
        insert_analysis_result(campaign.campaign_id, run_id, result)
    return result
```

**Logging pattern** — copy from `llm.py` line 19:

```python
# llm.py line 19 — module-level logger, same pattern for api/main.py
logger = logging.getLogger(__name__)
```

---

### `api/models.py` (model, request-response)

**Analog:** `llm.py` lines 28–53 — Pydantic v2 `BaseModel` + `Field` definitions

**Imports pattern** (from `llm.py` lines 1–17, subset):

```python
# llm.py lines 6-7 — Pydantic imports convention
from pydantic import BaseModel, Field
```

**Core model pattern** — copy field declaration style from `llm.py` lines 28–53:

```python
# llm.py lines 28-42 — CampaignAction: typed fields, Field() descriptions, Literal for enums
class CampaignAction(BaseModel):
    campaign_id: str = Field(description="Matches campaign_id from input CSV exactly")
    budget_action: Literal["increase", "pause", "decrease", "insufficient_data"]
    percentage_change: int = Field(
        description="Signed integer -100 to +100. pause=-100, insufficient_data=0."
    )
    semantic_reasoning: str = Field(
        description="One sentence citing specific language from sales notes."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Signal consistency across sessions. 0.0=none, 1.0=unanimous.",
    )
    evidence_count: int = Field(
        description="Echo session_count from input. Do not hallucinate."
    )

# llm.py lines 47-53 — AnalysisResult: list field, Field() descriptions
class AnalysisResult(BaseModel):
    executive_summary: str = Field(
        description="2-3 sentence summary of portfolio health and the single most important action."
    )
    campaigns: list[CampaignAction] = Field(
        description="One CampaignAction per campaign in the input CSV. All campaigns must be included."
    )
```

New `api/models.py` uses the same pattern for request-body models (no `Field(description=...)` required since these are input models, not LLM response schemas):

```python
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

**Critical:** Do NOT import or redefine `AnalysisResult` here. Import it directly from `llm.py` in `api/main.py`. Redefining creates schema drift (documented in RESEARCH.md anti-patterns).

---

### `api/db.py` (service, CRUD)

**Analog:** `data.py` lines 1–57 — function-per-operation decomposition, typed returns, raises on semantic error

**Imports pattern** — `data.py` lines 1–6 show the convention (stdlib + one library per logical group):

```python
# data.py lines 1-2 — stdlib imports first, then library
import pathlib
import pandas as pd
```

`api/db.py` follows the same order:

```python
import os

import psycopg2
import psycopg2.extras  # required: Json adapter + JSONB auto-deserialization
from psycopg2.extras import Json
```

**Core CRUD pattern** — no ORM analog in codebase; use RESEARCH.md Pattern 3 + full db.py skeleton from Code Examples section verbatim. Key structural points extracted from RESEARCH.md lines 547–650:

```python
# Pattern: get_conn() — one connection per call, caller closes
def get_conn():
    """Open a new connection. Caller is responsible for close()."""
    return psycopg2.connect(os.environ["DATABASE_URL"])

# Pattern: try/finally conn.close() — prevents connection leak (see Pitfall 3)
def insert_analysis_result(campaign_id: str, run_id: str, result) -> None:
    conn = get_conn()
    try:
        with conn:                           # transaction context (commit/rollback)
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
        conn.close()                         # closes connection (with conn: does NOT close it)
```

**Schema initialization pattern** — `init_db()` called at lifespan startup; uses `CREATE TABLE IF NOT EXISTS` (idempotent):

```python
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
```

**Error handling pattern** — `data.py` lines 23–32 show the pattern: let domain errors propagate to the caller (no swallowing):

```python
# data.py lines 23-32 — no try/except; MergeError propagates to caller
# api/main.py catches it and maps to 422
merged_df = pd.merge(
    web_df, crm_df,
    on=["session_id", "campaign_id"],
    how="inner",
    validate="m:1",
)
```

Same principle in `api/db.py`: psycopg2 `OperationalError` and `IntegrityError` propagate; FastAPI converts uncaught exceptions to 500.

---

### `Dockerfile` (config — rewrite adding `api` target)

**Analog:** `Dockerfile` lines 1–51 — existing single-stage builder pattern

**Builder stage pattern** — `Dockerfile` lines 1–25 (copy exactly, this stage is shared):

```dockerfile
# syntax=docker/dockerfile:1.7

# ---- builder stage ----
FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# First pass: install dependencies only (cache key = lockfile only)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Copy source code
COPY . /app

# Second pass: install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
```

**Runtime stage pattern** — `Dockerfile` lines 27–51 (existing `streamlit` target; `api` target copies this pattern exactly, changing only EXPOSE and CMD):

```dockerfile
# ---- runtime stage (existing pattern — becomes "streamlit" target) ----
FROM python:3.11-slim-bookworm AS streamlit    # ADD "AS streamlit" to existing line 28

# Non-root user pattern — lines 30-32 (copy exactly)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8501

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ---- api runtime (new target — same non-root pattern, different EXPOSE + CMD) ----
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

**Critical edit:** Existing `Dockerfile` line 28 is `FROM python:3.11-slim-bookworm` with no target name. This MUST be changed to `FROM python:3.11-slim-bookworm AS streamlit`. Without a named target, `compose.yaml` `target: streamlit` will fail.

---

### `compose.yaml` (config — additive modification)

**Analog:** `compose.yaml` lines 1–32 — existing service definition format

**Existing service pattern to preserve** — `compose.yaml` lines 2–8:

```yaml
# compose.yaml lines 2-8 — app service pattern: build, restart, env_file, networks
  app:
    build: .                   # MUST change to "build: { context: ., target: streamlit }"
    restart: unless-stopped
    env_file: .env
    networks:
      - internal
```

**Required change to `app` service** (Pitfall 1 from RESEARCH.md): Change `build: .` to explicit target:

```yaml
  app:
    build:
      context: .
      target: streamlit        # required after Dockerfile gains multiple targets
    restart: unless-stopped
    env_file: .env
    networks:
      - internal
```

**New `fastapi` service** — follows `app` service pattern, adds `depends_on`:

```yaml
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
```

**New `postgres` service** — follows `caddy` service pattern (image + volumes + networks), internal-only (no `ports:`):

```yaml
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: performance_plus
      POSTGRES_USER: ppuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}    # from .env, never hardcoded
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal
    # No ports: — internal only per D-08
```

**Existing caddy volumes pattern** — `compose.yaml` lines 29–31 (extend, do not replace):

```yaml
# compose.yaml lines 29-31 — existing volume declarations; add postgres_data alongside
volumes:
  caddy_data:
  caddy_config:
  postgres_data:               # new
```

---

### `pyproject.toml` (config — additive modification)

**Analog:** `pyproject.toml` lines 6–13 — existing dependency declaration format

**Existing pattern** — `pyproject.toml` lines 6–13:

```toml
# pyproject.toml lines 6-13 — version pin format: ">=X.Y,<Z.0" with upper bound
dependencies = [
  "streamlit>=1.40,<2.0",
  "pandas>=2.2.3,<2.3",
  "python-dotenv>=1.0",
  "openai>=1.50,<2.0",
  "pydantic>=2.8,<3.0",
  "tenacity>=8.5",
]
```

New dependencies follow the same `">=X.Y,<Z.0"` format with upper bound:

```toml
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.29,<1.0",
  "psycopg2-binary>=2.9,<3.0",
```

Dev dependency addition follows `pyproject.toml` lines 16–20 pattern (already have httpx 0.28.1 in venv; add to `[dependency-groups] dev` explicitly):

```toml
[dependency-groups]
dev = [
  "ruff>=0.6",
  "pytest>=8",
  "pyyaml>=6.0.3",
  "httpx>=0.27,<1.0",    # new — TestClient for FastAPI endpoint tests
]
```

**Install command** (not hardcoded in file, but for planner reference):
```bash
uv add "fastapi>=0.115,<1.0" "uvicorn[standard]>=0.29,<1.0" "psycopg2-binary>=2.9,<3.0"
uv add --dev "httpx>=0.27,<1.0"
```

---

### `.env.example` (config — additive modification)

**Analog:** `.env.example` lines 1–2 — `KEY=value` format, blank value as placeholder

**Existing pattern** — `.env.example` lines 1–2:

```bash
# .env.example lines 1-2 — blank value placeholder (not example value, not quotes)
OPENAI_API_KEY=your-key-here
DEMO_MODE=
```

New vars follow the same convention:

```bash
API_KEY=your-api-key-here
DATABASE_URL=postgresql://ppuser:password@postgres:5432/performance_plus
POSTGRES_PASSWORD=your-postgres-password-here
```

---

## Shared Patterns

### Pattern S1: Module-Level Logger

**Source:** `llm.py` line 19
**Apply to:** `api/main.py`, `api/db.py`

```python
# llm.py line 19
logger = logging.getLogger(__name__)
```

### Pattern S2: Pydantic v2 BaseModel Field Declarations

**Source:** `llm.py` lines 28–53
**Apply to:** `api/models.py` (WebSession, CrmRecord, AnalyzeRequest, CrmWebhookRecord)

```python
# llm.py lines 28-31 — pattern: typed field, no default = required, Field() only for constraints
class CampaignAction(BaseModel):
    campaign_id: str = Field(description="Matches campaign_id from input CSV exactly")
    budget_action: Literal["increase", "pause", "decrease", "insufficient_data"]
    percentage_change: int = Field(
        description="Signed integer -100 to +100. pause=-100, insufficient_data=0."
    )
```

Input models in `api/models.py` use the same BaseModel but omit `Field(description=...)` since they are not LLM response schemas.

### Pattern S3: Non-Root Docker User

**Source:** `Dockerfile` lines 30–32
**Apply to:** Both `streamlit` and `api` runtime stages in rewritten Dockerfile

```dockerfile
# Dockerfile lines 30-32 — non-root user with home dir (critical for appuser home writes)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser
```

### Pattern S4: uv sync in Docker Builder

**Source:** `Dockerfile` lines 15–25
**Apply to:** Builder stage — unchanged in Phase 5 rewrite

```dockerfile
# Dockerfile lines 15-25 — two-pass uv sync: deps first (cache-friendly), then project
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
```

### Pattern S5: DEMO_MODE + Null Client Guard

**Source:** `llm.py` lines 21–22 and 99–100
**Apply to:** `tests/test_api.py` (use same `monkeypatch.setenv("DEMO_MODE", "1") + monkeypatch.setattr("llm.client", None)` pattern from `tests/test_llm.py` line 139–140)

```python
# llm.py lines 21-22 — client is None when OPENAI_API_KEY not set
_env_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=_env_key) if _env_key else None

# llm.py lines 99-100 — DEMO_MODE bypass check
if os.environ.get("DEMO_MODE") == "1" and client is None:
    return _load_fixture()
```

### Pattern S6: Test Fixture Pattern (mock + monkeypatch)

**Source:** `tests/test_llm.py` lines 1–6, 47–53, 139–146
**Apply to:** `tests/test_api.py`

```python
# tests/test_llm.py lines 1-6 — test imports pattern
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
import llm
from llm import run_analysis, CampaignAction, AnalysisResult

# tests/test_llm.py lines 47-53 — @patch decorator + MagicMock return value pattern
@patch("llm.client")
def test_run_analysis_returns_analysis_result(mock_client):
    expected = _make_valid_analysis_result()
    mock_client.beta.chat.completions.parse.return_value = _make_mock_completion(parsed=expected)
    result = run_analysis(_minimal_agg_df())
    assert isinstance(result, AnalysisResult)
```

For `tests/test_api.py`, the equivalent pattern uses `TestClient` (not `@patch` on `llm.client` directly):

```python
# tests/test_llm.py lines 139-146 — monkeypatch env + client pattern for DEMO_MODE tests
def test_demo_mode_returns_fixture(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setattr("llm.client", None)
    ...
```

---

## No Analog Found

All files have analogs. The following files have **partial analogs only** (assembled from multiple sources):

| File | Role | Data Flow | Gap |
|---|---|---|---|
| `api/main.py` | controller | request-response | No existing FastAPI controller in codebase; auth dependency pattern (`APIKeyHeader`) has no local analog — use RESEARCH.md Pattern 1 verbatim |
| `api/db.py` | service | CRUD | No existing psycopg2 code in codebase; all SQL patterns come from RESEARCH.md Code Examples section — use the full `db.py` skeleton from RESEARCH.md lines 547–650 |

---

## Critical Sequencing Notes for Planner

1. **`Dockerfile` and `compose.yaml` must be updated atomically.** The moment `Dockerfile` gains the `AS streamlit` and `AS api` named targets, `compose.yaml` line 3 (`build: .`) becomes incorrect (Docker will default to the last stage, `api`, for the `app` service). Both files must change in the same commit/step.

2. **`uv add` before Dockerfile build.** `pyproject.toml` and `uv.lock` must include `fastapi`, `uvicorn[standard]`, `psycopg2-binary` before `docker build` runs, because the builder stage runs `uv sync --locked`.

3. **`api/db.py` `init_db()` must exist before `api/main.py` `lifespan` references it.** Write `api/db.py` first.

4. **`api/models.py` must exist before `api/main.py`** imports `AnalyzeRequest` and `CrmWebhookRecord` from it.

---

## Metadata

**Analog search scope:** `/Users/rukesh/Documents/Dev/performance_plus/` — all Python source files, Dockerfile, compose.yaml, pyproject.toml, .env.example
**Files scanned:** `llm.py`, `data.py`, `Dockerfile`, `compose.yaml`, `pyproject.toml`, `.env.example`, `tests/test_llm.py`, `tests/test_data.py`
**Pattern extraction date:** 2026-06-01
