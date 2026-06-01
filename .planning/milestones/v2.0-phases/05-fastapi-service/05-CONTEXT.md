# Phase 5: FastAPI Service - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a FastAPI service that exposes five endpoints for external clients (n8n, CRM webhooks, API consumers) to send session data and receive structured gpt-4o budget action recommendations. Results are persisted in Postgres so they can be retrieved later. API key auth (X-API-Key header) protects all endpoints except /api/health.

Phase 5 scope: FastAPI code (`api/` package), Postgres schema + psycopg2 wiring, two-target Dockerfile, Postgres service added to `compose.yaml`. No Caddy routing changes (Phase 8). No waitlist table (Phase 6). No UI changes.

</domain>

<decisions>
## Implementation Decisions

### API Input Shape
- **D-01:** `POST /api/analyze` accepts **two separate arrays** in the JSON body: `web_sessions[]` and `crm_records[]`. The server merges on `session_id` + `campaign_id` and aggregates using the existing `data.py` logic (`pd.merge` inner join + `compute_campaign_agg()`).
- **D-02:** Both arrays use **the same column names as the existing CSV schema** — no renaming. `web_sessions` fields: `session_id, campaign_id, clicks, impressions, cost_usd, conversion_rate`. `crm_records` fields: `session_id, campaign_id, lead_status, projected_value, sales_notes`.
- **D-03:** Response shape is the **existing `AnalysisResult` model directly**: `executive_summary` (str) + `campaigns` (list[CampaignAction]). No wrapper envelope. Consistent with Streamlit output, zero extra serialization.

### FastAPI Code Layout
- **D-04:** FastAPI code lives in an **`api/` package at the project root** — `api/__init__.py`, `api/main.py`, `api/models.py`, `api/db.py`. The package imports `llm.py` and `data.py` from the parent directory.
- **D-05:** **Single `Dockerfile` with two build targets**: `streamlit` target runs `streamlit run app.py`; `api` target runs `uvicorn api.main:app --host 0.0.0.0 --port 8000`. Existing `Dockerfile` is rewritten as a multi-stage file. `compose.yaml` references `target: streamlit` and `target: api` respectively.

### Webhook Ingestion
- **D-06:** `POST /api/webhook/crm` accepts a **single CRM record** with the same schema as one element of `crm_records[]` (session_id, campaign_id, lead_status, projected_value, sales_notes). Returns 202 immediately.
- **D-07:** After acknowledging, the webhook payload is **stored in a `pending_sessions` Postgres table** for deferred analysis. Analysis is not triggered inline — it happens when a client later calls `POST /api/analyze`. This decouples webhook ingestion from potentially slow gpt-4o calls.

### Postgres Scope
- **D-08:** Phase 5 **adds a `postgres` service to `compose.yaml`** so the FastAPI service can be tested locally end-to-end before Phase 8 wires Caddy routing. The postgres service uses `postgres:16-alpine`, mounts a named volume, and is internal-only (not exposed on host).
- **D-09:** Database interactions use **psycopg2 + raw parameterized SQL**. No ORM. Connection string loaded from `DATABASE_URL` env var.
- **D-10:** Analysis results are stored with **one row per campaign per analysis run** in an `analysis_results` table: `id (serial PK), campaign_id (text), run_id (UUID), analyzed_at (timestamptz), result_json (JSONB)`. `GET /api/campaigns/{campaign_id}/actions` queries `WHERE campaign_id = $1 ORDER BY analyzed_at DESC LIMIT 1`.
- **D-11:** `pending_sessions` table schema (webhook ingestion): `id (serial PK), campaign_id (text), session_id (text), lead_status (text), projected_value (numeric), sales_notes (text), received_at (timestamptz)`.

### Auth
- **D-12:** Auth is a **FastAPI dependency** that reads the `X-API-Key` header and compares it to the `API_KEY` env var. Returns 401 if missing or mismatched. Applied to POST /api/analyze, POST /api/webhook/crm, and GET /api/campaigns/{campaign_id}/actions. `/api/health` has no auth dependency (already decided in STATE.md).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stack & Existing App
- `./CLAUDE.md` — Authoritative on: Python 3.11, uv, multi-stage Dockerfile pattern, `python:3.11-slim-bookworm` base, `uv sync --frozen --no-dev`, non-root user, Caddy routing decisions, `OPENAI_API_KEY` env var handling. Read "TL;DR", "Dockerfile", "Recommended Stack", and "What NOT to Use" sections.
- `.planning/PROJECT.md` — Constraints and v2.0 goal. Confirms self-hosted VPS + Docker, no Coolify.
- `.planning/ROADMAP.md` — Phase 5 success criteria (5 items that must be TRUE); requirements API-01 through API-05.
- `.planning/REQUIREMENTS.md` §API Integration — API-01 through API-05 full requirement text.

### Existing Code (reuse + integration)
- `./llm.py` — `CampaignAction` + `AnalysisResult` Pydantic models; `run_analysis(campaign_agg: pd.DataFrame) -> AnalysisResult`; `MODEL` constant. FastAPI imports these directly.
- `./data.py` — `compute_campaign_agg(merged_df: pd.DataFrame) -> pd.DataFrame`; `pd.merge` inner join pattern with `validate="m:1"`. FastAPI uses both for the server-side merge + aggregate on incoming two-array payload.
- `./compose.yaml` — Current two-service compose (app + caddy). Phase 5 adds `fastapi` and `postgres` services. Phase 8 updates Caddy routing — do NOT modify Caddyfile in Phase 5.

### Phase 4 Context (deploy patterns)
- `.planning/phases/04-deploy-and-ship/04-CONTEXT.md` — D-12/D-13: multi-stage Dockerfile pattern, non-root user, container entrypoint format. Replicate these patterns for the `api` target.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `llm.CampaignAction` + `llm.AnalysisResult`: Pydantic v2 models — used as FastAPI response schemas directly. No redefinition needed in `api/models.py` (import from parent `llm.py`).
- `llm.run_analysis(campaign_agg)`: Core gpt-4o call. FastAPI endpoint calls this after merge + aggregate.
- `data.compute_campaign_agg(merged_df)`: Aggregation logic. FastAPI uses this after merging the two input arrays.
- `pyproject.toml` + `uv.lock`: Add `fastapi`, `uvicorn[standard]`, `psycopg2-binary` here. No separate lock file needed.

### Established Patterns
- `uv run` for all shell invocations (bare python not on PATH).
- Env vars via `.env` file + `python-dotenv` (or `compose.yaml` `env_file:`). New vars to add: `API_KEY`, `DATABASE_URL`.
- Non-root Docker user pattern (from Phase 4 Dockerfile).
- Tenacity retry already wraps the gpt-4o call in `llm.py` — FastAPI doesn't need its own retry layer.

### Integration Points
- New package: `api/` (main.py, models.py, db.py, __init__.py)
- Modified files: `Dockerfile` (add `api` target), `compose.yaml` (add `fastapi` + `postgres` services), `pyproject.toml` (add FastAPI deps), `.env.example` (add `API_KEY`, `DATABASE_URL`)
- The FastAPI service does NOT import from `app.py` or `ui_helpers.py` — only from `llm.py` and `data.py`

</code_context>

<specifics>
## Specific Ideas

- The `POST /api/analyze` merge should use the same `validate="m:1"` guard as `data.py` — if the incoming arrays have duplicate session_ids in the CRM records, return a 422 with a descriptive error rather than silently bloating.
- `GET /api/health` response body: `{ "status": "ok", "version": "2.0.0", "service": "performance-plus-api" }` — simple, no auth.
- The `pending_sessions` table is a Phase 5 stub. Full "analyze pending sessions" logic (batch processing the queue) is a future phase. Phase 5 just needs: insert on webhook, table exists.

</specifics>

<deferred>
## Deferred Ideas

- **Batch processing of pending_sessions** — Automatically analyze all pending webhook sessions on a schedule or trigger. Phase 5 only stores them; actual batch analysis is a future phase.
- **Rate limiting per API key** — Not in Phase 5 scope. Single shared API key for v2.0.
- **Async FastAPI + asyncpg** — psycopg2 sync is the Phase 5 choice. Migrating to async is a future optimization.
- **Caddy routing for /api** — Intentionally deferred to Phase 8. Phase 5 service runs on port 8000, accessible locally; Phase 8 wires Caddy.

</deferred>

---

*Phase: 5-FastAPI Service*
*Context gathered: 2026-06-01*
