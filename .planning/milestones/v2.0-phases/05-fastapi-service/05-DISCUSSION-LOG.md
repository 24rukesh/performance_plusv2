# Phase 5: FastAPI Service - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-01
**Phase:** 5-FastAPI Service
**Areas discussed:** API input shape, FastAPI code layout, Webhook ingestion behavior, Postgres scope

---

## API Input Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Campaign-level aggregate | Client sends already-rolled-up rows; matches run_analysis() directly | |
| Session-level rows (pre-merged) | Client sends merged CRM+analytics sessions; server aggregates | |
| Two separate arrays | Client sends web_sessions[] + crm_records[]; server merges + aggregates | ✓ |

**User's choice:** Two separate arrays (web_sessions + crm_records)

| Option | Description | Selected |
|--------|-------------|----------|
| Match existing CSV schema | Same column names as web_analytics.csv and crm_data.csv | ✓ |
| Normalized API names | camelCase or REST-idiomatic naming with a mapping layer | |
| You decide | Downstream agents pick column names | |

**User's choice:** Match existing CSV schema

| Option | Description | Selected |
|--------|-------------|----------|
| Same AnalysisResult shape | Return existing Pydantic model: executive_summary + campaigns[] | ✓ |
| Wrapped envelope | { status, request_id, data: AnalysisResult } | |
| You decide | Downstream agents pick response shape | |

**User's choice:** Same AnalysisResult shape

**Notes:** User wants the server to own the merge/aggregate logic (reusing data.py), keeping client integration simple — send two raw exports, get back the same JSON shape the Streamlit app produces.

---

## FastAPI Code Layout

| Option | Description | Selected |
|--------|-------------|----------|
| api/ package at project root | __init__.py, main.py, models.py, db.py; imports llm.py and data.py | ✓ |
| Single api.py at project root | Everything flat alongside app.py | |
| Separate backend/ directory | Own pyproject.toml, fully isolated, can't import llm.py directly | |

**User's choice:** api/ package at project root

| Option | Description | Selected |
|--------|-------------|----------|
| New Dockerfile.api alongside existing Dockerfile | Separate file per service | |
| Single Dockerfile with two build targets | streamlit target + api target in one file | ✓ |
| You decide | Downstream agents pick Dockerfile strategy | |

**User's choice:** Single Dockerfile with two build targets

**Notes:** Prefers keeping code in the same repo and sharing the Dockerfile to avoid duplicating the base image setup.

---

## Webhook Ingestion Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Store and defer | Save to pending_sessions table; analysis deferred to future /api/analyze call | ✓ |
| Store and immediately analyze | Run gpt-4o inline, could timeout; couples webhook to slow call | |
| Acknowledge only, no DB | Return 202 and discard; placeholder only | |

**User's choice:** Store and defer

| Option | Description | Selected |
|--------|-------------|----------|
| Same schema as CRM array in /api/analyze | session_id, campaign_id, lead_status, projected_value, sales_notes | ✓ |
| Generic key-value envelope | { source, payload: {} }; flexible but requires mapping layer | |
| You decide | Downstream agents define webhook schema | |

**User's choice:** Same schema as CRM records in /api/analyze

**Notes:** Consistent schema across endpoints means n8n can use the same CRM export format for both the analyze endpoint and the webhook.

---

## Postgres Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Add Postgres to compose.yaml now | postgres service in compose; testable locally before Phase 8 | ✓ |
| Code only — defer compose to Phase 8 | Write FastAPI + DB code but run local Postgres separately for testing | |

**User's choice:** Add Postgres to compose.yaml now

| Option | Description | Selected |
|--------|-------------|----------|
| psycopg2 + raw SQL | Direct parameterized SQL; minimal deps; hackathon velocity | ✓ |
| SQLAlchemy ORM | Full ORM; more boilerplate; better long-term | |
| SQLModel | Pydantic + SQLAlchemy hybrid; elegant but less common | |

**User's choice:** psycopg2 + raw SQL

| Option | Description | Selected |
|--------|-------------|----------|
| One row per campaign per analysis run | analysis_results: id, campaign_id, run_id, analyzed_at, result_json | ✓ |
| One row per run, JSONB array | analysis_runs: run_id, analyzed_at, result_json (full AnalysisResult) | |
| You decide | Downstream agents design schema per success criteria | |

**User's choice:** One row per campaign per analysis run

**Notes:** Normalized by campaign_id makes GET /api/campaigns/{campaign_id}/actions a simple indexed query.

---

## Claude's Discretion

None — user made explicit choices on all questions.

## Deferred Ideas

- Batch processing of pending_sessions (analyze the queue automatically)
- Rate limiting per API key
- Async FastAPI + asyncpg migration
- Caddy routing for /api (Phase 8)
