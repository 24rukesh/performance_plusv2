---
phase: 12-analysis-persistence
plan: "05"
subsystem: database
tags: [postgres, psycopg2, streamlit, pytest, monkeypatch, demo_mode, init_db, fallback]

# Dependency graph
requires:
  - phase: 12-analysis-persistence
    provides: st_db.py persistence module, init_db() startup call, save button, test_evals.py fallback tests

provides:
  - Guarded init_db() startup: app degrades gracefully when DATABASE_URL absent or Postgres unreachable
  - Expanded save button except clause covering both RuntimeError and psycopg2.OperationalError
  - Env-hardened fallback eval tests deterministic across all CI environments including DEMO_MODE=1

affects:
  - app.py startup reliability
  - test_evals.py CI determinism

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "try/except (RuntimeError, psycopg2.OperationalError) wrapping optional DB calls at startup"
    - "monkeypatch.delenv + monkeypatch.setattr for environment-deterministic test isolation"

key-files:
  created: []
  modified:
    - app.py
    - tests/test_evals.py

key-decisions:
  - "CR-01: init_db() wrapped in try/except at module startup — app degrades gracefully without crashing Streamlit"
  - "WR-02: save button except expanded to (psycopg2.OperationalError, RuntimeError) — covers missing DATABASE_URL path via st_db.get_conn() raising RuntimeError"
  - "WR-03: monkeypatch.delenv('DEMO_MODE', raising=False) + setattr('llm.client', MagicMock()) added to both fallback tests — makes tests deterministic in DEMO_MODE=1 environments"

patterns-established:
  - "Pattern: DB-optional startup — wrap optional init calls in try/except and log warning; never let infrastructure failures block app boot"
  - "Pattern: Env-hardened tests — always monkeypatch away env vars that can trigger early returns in the function under test"

requirements-completed:
  - MGMT-01
  - MGMT-03

# Metrics
duration: 5min
completed: 2026-06-04
---

# Phase 12 Plan 05: init_db Startup Guard + Test Env Hardening Summary

**Three gap-closure fixes: init_db() startup guarded with try/except for Postgres-absent resilience, save button expanded to catch RuntimeError, and eval fallback tests hardened with DEMO_MODE env isolation**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-04T09:02:00Z
- **Completed:** 2026-06-04T09:07:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- CR-01 closed: app.py no longer crashes on startup when DATABASE_URL is absent or Postgres is unreachable — init_db() wrapped in try/except with warning log
- WR-02 closed: save button except clause now catches both psycopg2.OperationalError and RuntimeError, preventing raw tracebacks when DATABASE_URL is not configured
- WR-03 closed: both fallback eval tests in test_evals.py are now deterministic — pass in all environments regardless of DEMO_MODE env var state
- Full test suite: 139 passed, 5 skipped — no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Guard init_db() startup and expand save button except clause** - `200d31d` (fix)
2. **Task 2: Harden fallback tests with DEMO_MODE guard and client mock** - `3eb9568` (fix)

## Files Created/Modified

- `app.py` - Added try/except around init_db() call at lines 19-21; expanded save button except clause at line 541 to include RuntimeError
- `tests/test_evals.py` - Added `monkeypatch.delenv("DEMO_MODE", raising=False)` and `monkeypatch.setattr("llm.client", MagicMock())` to both test_openai_error_triggers_fallback and test_value_error_does_not_trigger_fallback

## Decisions Made

- Exception order in init_db() guard is (RuntimeError, psycopg2.OperationalError) — RuntimeError first as it is raised earlier (by get_conn() when DATABASE_URL absent), psycopg2.OperationalError when DB is configured but unreachable
- Exception order in save button guard is (psycopg2.OperationalError, RuntimeError) — maintained existing order for save, added RuntimeError to cover missing DATABASE_URL case
- Used `import logging as _logging` inside the except block to avoid polluting module namespace (standard library, no new dep)
- `monkeypatch.setattr("llm.client", MagicMock())` prevents run_analysis() DEMO_MODE early return triggered by None-client guard — does not affect _call_llm patch since _call_llm raises before client is used

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All Phase 12 gaps closed (CR-01, WR-02, WR-03 from 12-VERIFICATION.md)
- v3.0 milestone complete — all phases (9-12) delivered, 139 tests passing
- App is fully resilient to Postgres unavailability at startup and during save operations
- Eval test suite is deterministic across all CI environments

## Known Stubs

None.

## Threat Flags

No new security-relevant surface introduced. Existing threat mitigations from plan applied:

| Threat ID | Mitigated | Description |
|-----------|-----------|-------------|
| T-12-05-01 | Yes | init_db() wrapped in try/except — DoS via startup crash prevented |
| T-12-05-02 | Yes | Save button catches RuntimeError — no raw traceback information disclosure |

---
*Phase: 12-analysis-persistence*
*Completed: 2026-06-04*

## Self-Check: PASSED

- `app.py` modified: FOUND (git status confirms 200d31d)
- `tests/test_evals.py` modified: FOUND (git status confirms 3eb9568)
- Commit 200d31d exists: FOUND
- Commit 3eb9568 exists: FOUND
- 139 passed, 5 skipped: VERIFIED
- Both except clauses in app.py: VERIFIED (lines 23, 541)
- 2 monkeypatch.delenv occurrences in test_evals.py: VERIFIED
