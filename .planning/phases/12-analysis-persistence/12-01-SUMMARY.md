---
phase: 12
plan: "12-01"
title: "st_db.py — Postgres persistence module"
subsystem: data-layer
tags: [postgres, psycopg2, persistence, crud, unit-tests]
completed_date: "2026-06-04"
duration_minutes: 5

dependency_graph:
  requires: []
  provides:
    - st_db.get_conn
    - st_db.init_db
    - st_db.save_analysis
    - st_db.list_analyses
    - st_db.load_analysis
    - st_db.delete_analysis
    - st_db._log_analysis_run
  affects:
    - app.py (plan 12-03 imports st_db)
    - llm.py (plan 12-02 calls _log_analysis_run)

tech_stack:
  added: []
  patterns:
    - "psycopg2 double-context-manager (with conn / with conn.cursor() as cur / finally conn.close())"
    - "Json() adapter for JSONB column inserts"
    - "RETURNING id for INSERT with auto-generated PK"
    - "psycopg2 JSONB auto-deserialization on SELECT"
    - "try/except psycopg2.Error: pass in logging function"

key_files:
  created:
    - path: "st_db.py"
      description: "Postgres persistence module — 7 CRUD functions for analysis_runs + analysis_logs"
    - path: "tests/test_st_db.py"
      description: "8 unit tests for all CRUD functions with mocked psycopg2"
  modified: []

decisions:
  - "Single try/except psycopg2.Error wraps the entire _log_analysis_run body including get_conn() — this ensures even a connection failure during logging is silently swallowed"
  - "init_db() runs both CREATE TABLE IF NOT EXISTS statements in a single conn/cursor block per D-02 and AI-SPEC §7 — one transaction, two DDL statements"
  - "load_analysis raises RuntimeError (not KeyError or psycopg2 error) when run_id not found — clean API for app.py callers"
  - "list_analyses returns datetime objects natively from psycopg2 (not stringified) — callers call .strftime() directly per CONTEXT.md D-11 pattern"

metrics:
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
  test_results: "8 passed, 0 failed"
---

# Phase 12 Plan 01: st_db.py — Postgres Persistence Module Summary

**One-liner:** psycopg2 CRUD module for analysis_runs + analysis_logs using the same double-context-manager pattern as api/db.py, with 8 mocked unit tests.

## What Was Built

### st_db.py (repo root)

A standalone Postgres persistence module with 7 functions:

| Function | Role |
|----------|------|
| `get_conn()` | Reads DATABASE_URL, raises RuntimeError if missing, returns psycopg2 connection |
| `init_db()` | Creates analysis_runs and analysis_logs tables idempotently (CREATE TABLE IF NOT EXISTS) |
| `save_analysis(label, payload)` | Inserts into analysis_runs using Json(payload) for JSONB, returns new int id via RETURNING id |
| `list_analyses()` | Selects id, label, saved_at ORDER BY saved_at DESC, returns list[dict] |
| `load_analysis(run_id)` | Returns payload JSONB (auto-deserialized by psycopg2), raises RuntimeError if not found |
| `delete_analysis(run_id)` | Executes DELETE FROM analysis_runs WHERE id = %s |
| `_log_analysis_run(...)` | Inserts into analysis_logs; silently swallows psycopg2.Error |

Every function (except get_conn) uses the canonical double-context-manager pattern from api/db.py:
```python
conn = get_conn()
try:
    with conn:
        with conn.cursor() as cur:
            ...
finally:
    conn.close()
```

### tests/test_st_db.py

8 unit tests, all using `unittest.mock.patch("st_db.psycopg2.connect")`:

| Test | What It Verifies |
|------|-----------------|
| test_get_conn_raises_when_no_env | RuntimeError raised when DATABASE_URL absent |
| test_init_db_executes_create_tables | cursor.execute called twice with CREATE TABLE IF NOT EXISTS |
| test_save_analysis_returns_id | Returns 42 from (42,) fetchone; Json adapter used in params |
| test_list_analyses_returns_list_of_dicts | Rows mapped to [{"id", "label", "saved_at"}] with datetime preserved |
| test_load_analysis_returns_payload | Returns row[0] dict from fetchone |
| test_load_analysis_raises_when_not_found | RuntimeError raised when fetchone returns None |
| test_delete_analysis_executes_delete | DELETE with correct id param (5,) |
| test_log_analysis_run_swallows_psycopg2_error | No exception raised when connect raises OperationalError |

## Verification

```
uv run pytest tests/test_st_db.py -x -q
........
8 passed in 0.03s
```

## Deviations from Plan

None — plan executed exactly as written.

The `_log_analysis_run` error guard wraps the entire function body (including `get_conn()`) rather than just the cursor operations. This is the correct implementation: if `get_conn()` raises (e.g. DATABASE_URL not set, connection refused), the except clause catches it. This matches the plan's stated intent that "observability must not crash the app."

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundaries introduced in this plan. `st_db.py` reads DATABASE_URL from environment (T-12-02 — mitigated per plan threat model). No new packages installed.

## Self-Check: PASSED

- [x] st_db.py exists at worktree root: FOUND
- [x] tests/test_st_db.py exists: FOUND
- [x] Task 1 commit be1dffa: FOUND
- [x] Task 2 commit ac5c1f2: FOUND
- [x] All 8 tests pass: VERIFIED (8 passed, 0 failed)
- [x] All 7 functions exported: VERIFIED
