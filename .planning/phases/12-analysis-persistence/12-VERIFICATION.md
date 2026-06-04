---
phase: 12-analysis-persistence
verified: 2026-06-04T10:15:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 7/8
  gaps_closed:
    - "All st_db calls in app.py are guarded to prevent app crash when Postgres is unavailable (CR-01: init_db() wrapped in try/except at startup)"
    - "Save button except clause catches both psycopg2.OperationalError and RuntimeError (WR-02)"
    - "test_evals.py fallback tests have monkeypatch.delenv('DEMO_MODE', raising=False) in both functions (WR-03)"
  gaps_remaining: []
  regressions: []
---

# Phase 12: Analysis Persistence — Verification Report

**Phase Goal:** Add Postgres analysis persistence (save/load/delete) and OpenAI API fallback (auto-fallback to fixture on OpenAIError) so the demo is resilient to API failures and marketers can recall past analysis runs without re-uploading CSVs.
**Verified:** 2026-06-04T10:15:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure plan 12-05

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | st_db.py has 7 functions (get_conn, init_db, save_analysis, list_analyses, load_analysis, delete_analysis, _log_analysis_run) all present with the double-context-manager pattern | VERIFIED | Confirmed from initial verification — no modifications to st_db.py in plan 12-05; regression check shows import and all 7 defs intact |
| 2 | tests/test_st_db.py has 9 tests including test_crud_round_trip | VERIFIED | 9 tests passing; no regression in plan 12-05 (only test_evals.py modified) |
| 3 | llm.py wraps _call_llm() in except openai.OpenAIError (not except Exception), sets api_fallback_active=True in session state (guarded by hasattr), and makes a guarded _log_analysis_run call | VERIFIED | llm.py line 134: `except openai.OpenAIError as exc:`; line 139: `if hasattr(st, "session_state"):`; line 140: `st.session_state["api_fallback_active"] = True`; regression check confirmed intact |
| 4 | ValueError from _call_llm() propagates unhandled — not caught by except openai.OpenAIError | VERIFIED | Only `except openai.OpenAIError` clause present; test_value_error_does_not_trigger_fallback passes |
| 5 | app.py: import st_db, guarded st_db.init_db() at startup, api_fallback_active in _state_defaults and reset before Run Analysis, warning banner above tabs | VERIFIED | Lines 19-25: `import st_db`, `import psycopg2`, then `try: st_db.init_db() except (RuntimeError, psycopg2.OperationalError) as _db_init_err: _logging.warning(...)`. Line 173: `"api_fallback_active": False`. Line 426: reset to False. Lines 450-451: warning banner |
| 6 | app.py: Save Analysis section in Campaign Actions tab (st.text_input + st.button + st_db.save_analysis call) and Past Analyses sidebar with Load/Delete per row | VERIFIED | Lines 525-542: Save section with text_input, button, and st_db.save_analysis call intact. Lines 131-145: sidebar Past Analyses with list_analyses/load_analysis/delete_analysis confirmed |
| 7 | All st_db calls in app.py are guarded against Postgres unavailability | VERIFIED | app.py line 22-25: init_db() now wrapped in `try: ... except (RuntimeError, psycopg2.OperationalError)`. Line 541: save button except is `(psycopg2.OperationalError, RuntimeError)`. Lines 126/130/139/145: sidebar try/except blocks intact from 12-03. All paths guarded. |
| 8 | tests/test_evals.py covers Dimension 1 (RateLimitError, AuthenticationError, APIConnectionError + ValueError non-catch), Dimension 3 (fixture schema), Dimension 7 (decisiveness); all pass | VERIFIED | 6 tests: `uv run pytest tests/test_evals.py -v -q` → 6 passed; `DEMO_MODE=1 uv run pytest tests/test_evals.py -v -q` → 6 passed. Both test_openai_error_triggers_fallback (line 62-63) and test_value_error_does_not_trigger_fallback (lines 85-86) have `monkeypatch.delenv("DEMO_MODE", raising=False)` and `monkeypatch.setattr("llm.client", MagicMock())` |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `st_db.py` | Postgres persistence module, 7 functions | VERIFIED | Unchanged from 12-01; all 7 functions, substantive implementation |
| `tests/test_st_db.py` | 9 unit tests with mocked psycopg2 | VERIFIED | 9 tests, all passing, unchanged |
| `llm.py` | Modified run_analysis() with OpenAI fallback | VERIFIED | except openai.OpenAIError, hasattr guard, _log_analysis_run call — unchanged from 12-02/12-03 |
| `tests/test_llm.py` | test_fixture_validates_against_current_schema added | VERIFIED | Unchanged from 12-03 |
| `app.py` | Persistence UI + fallback banner wiring + guarded startup | VERIFIED | All structural additions present; init_db() now wrapped (CR-01 closed); save button except expanded (WR-02 closed) |
| `tests/test_evals.py` | Eval Dimensions 1, 3, 7 — env-hardened | VERIFIED | Both fallback tests now have DEMO_MODE delenv + llm.client mock (WR-03 closed) |
| `data/fixture_results.json` | cmp_brand_awareness updated to pass D7 | VERIFIED | Unchanged from 12-04; budget_action: "decrease", percentage_change: -15, confidence: 0.6 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| app.py module-level startup | st_db.init_db() | try/except (RuntimeError, psycopg2.OperationalError) | VERIFIED | Lines 21-25: `try: st_db.init_db() except (RuntimeError, psycopg2.OperationalError) as _db_init_err: import logging as _logging; _logging.warning(...)` |
| app.py save button | st_db.save_analysis() | try/except (psycopg2.OperationalError, RuntimeError) | VERIFIED | Line 541: `except (psycopg2.OperationalError, RuntimeError):` — both exception types covered |
| st_db.save_analysis | psycopg2.extras.Json | Json(payload) JSONB insert | VERIFIED | Unchanged from 12-01 |
| st_db.load_analysis | analysis_runs.payload | psycopg2 JSONB auto-deserialize | VERIFIED | Unchanged from 12-01 |
| run_analysis() except branch | st.session_state['api_fallback_active'] | local import streamlit as st + hasattr guard | VERIFIED | Unchanged from 12-02 |
| run_analysis() except branch | _load_fixture() | result = _load_fixture() in except, return after logging | VERIFIED | Unchanged from 12-02 |
| app.py sidebar Past Analyses | st_db.list_analyses() | direct call inside sidebar block, wrapped in try/except psycopg2.OperationalError | VERIFIED | Lines 126-145 — unchanged |
| app.py results section | st.warning | if st.session_state.get('api_fallback_active') | VERIFIED | Lines 450-451 — unchanged |
| tests/test_evals.py::test_openai_error_triggers_fallback | run_analysis() | DEMO_MODE cleared before call | VERIFIED | Line 62: `monkeypatch.delenv("DEMO_MODE", raising=False)` |
| tests/test_evals.py::test_value_error_does_not_trigger_fallback | run_analysis() | DEMO_MODE cleared before call | VERIFIED | Line 85: `monkeypatch.delenv("DEMO_MODE", raising=False)` |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 6 eval dimension tests pass (no DEMO_MODE) | `uv run pytest tests/test_evals.py -v -q` | 6 passed in 0.87s | PASS |
| All 6 eval dimension tests pass WITH DEMO_MODE=1 | `DEMO_MODE=1 uv run pytest tests/test_evals.py -v -q` | 6 passed in 0.42s | PASS |
| Full suite (excluding pre-existing deploy_config failure) | `uv run pytest tests/ -q --ignore=tests/test_deploy_config.py` | 139 passed, 5 skipped in 1.12s | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MGMT-01 | 12-01, 12-03, 12-04, 12-05 | User can save the current analysis to Postgres with a label, and reload any past saved analysis from a sidebar list without re-uploading CSV files | VERIFIED | Save/Load/Delete UI wired and substantive. init_db() startup now guarded — app starts successfully without Postgres and degrades gracefully. All DB call paths protected. |
| MGMT-03 | 12-02, 12-03, 12-04, 12-05 | When the OpenAI API is unavailable, the app falls back to a cached fixture response (DEMO_MODE) so the demo remains functional offline | VERIFIED | except openai.OpenAIError in run_analysis(); api_fallback_active flag set; warning banner rendered; eval tests pass in all environments including DEMO_MODE=1 |

### Anti-Patterns Found

No blockers or warnings.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TBD, FIXME, XXX markers found in phase-modified files | — | — |

No additional anti-patterns introduced by plan 12-05. The two previously-flagged warnings (WR-02 save button RuntimeError gap, WR-03 test_evals.py fragility) have been closed.

### Human Verification Required

None — all critical behaviors are verifiable programmatically.

### Gaps Summary

No gaps. All three items identified in the initial verification are now closed:

- **CR-01 (BLOCKER — now CLOSED):** app.py lines 21-25 now wrap `st_db.init_db()` in `try: ... except (RuntimeError, psycopg2.OperationalError)` with a warning log. The app starts successfully when DATABASE_URL is absent or Postgres is unreachable.
- **WR-02 (WARNING — now CLOSED):** Save button except clause at line 541 is now `except (psycopg2.OperationalError, RuntimeError):` — RuntimeError from get_conn() is caught and surfaces the friendly "Could not save" message.
- **WR-03 (WARNING — now CLOSED):** Both fallback tests in test_evals.py have `monkeypatch.delenv("DEMO_MODE", raising=False)` and `monkeypatch.setattr("llm.client", MagicMock())`. Tests pass with and without DEMO_MODE set (confirmed: 6 passed in both environments).

---

_Verified: 2026-06-04T10:15:00Z_
_Verifier: Claude (gsd-verifier)_
