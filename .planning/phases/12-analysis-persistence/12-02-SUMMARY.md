---
phase: 12
plan: "12-02"
subsystem: llm
tags: [fallback, openai-error, session-state, testing, demo-mode]
dependency_graph:
  requires: []
  provides: [run_analysis-openai-fallback, api_fallback_active-flag, _log_analysis_run-guarded-call]
  affects: [app.py-api_fallback_active-banner, tests/test_evals.py-fallback-selectivity-tests]
tech_stack:
  added: []
  patterns: [try/except openai.OpenAIError, local-import-streamlit-guard, hasattr-session-state-guard, guarded-st_db-import]
key_files:
  created: []
  modified:
    - llm.py
    - tests/test_llm.py
decisions:
  - "Assigned result = _load_fixture() inside except branch (not return) so _log_analysis_run fires for both success and fallback paths before returning"
  - "Used hasattr(st, 'session_state') guard + local import streamlit as st inside except branch to handle non-Streamlit test contexts"
  - "Guarded _log_analysis_run call with try/except Exception: pass so llm.py remains functional when st_db is not yet created (Plans 12-01 not yet run)"
  - "Added test_fixture_validates_against_current_schema as a new function (not augmenting test_fixture_schema) to satisfy plan done criteria explicitly"
metrics:
  duration: "1m 36s"
  completed: "2026-06-04T05:19:54Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 12 Plan 02: llm.py — OpenAI Error Fallback (DEMO_MODE Auto-Fallback) Summary

**One-liner:** `run_analysis()` now catches `openai.OpenAIError` after all tenacity retries, falls back to `_load_fixture()`, sets `api_fallback_active=True` in session state (guarded), and logs each run via a guarded `_log_analysis_run` call.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add try/except openai.OpenAIError to run_analysis() | aa3c8dc | llm.py |
| 2 | Add fallback selectivity tests to tests/test_llm.py | 40b9f3c | tests/test_llm.py |

## What Was Built

### Task 1: llm.py OpenAI Error Fallback

Modified `run_analysis()` in `llm.py` with the following structure:

1. Added `import openai` at module level (line 10) so `openai.OpenAIError` base class is accessible.
2. Added `_fallback_fired = False` and `_err_type = None` tracking variables after `csv_text`.
3. Wrapped `result = _call_llm(csv_text)` in `try:`.
4. Added `except openai.OpenAIError as exc:` branch that:
   - Sets `_fallback_fired = True` and `_err_type = type(exc).__name__`
   - Calls `logger.warning("OpenAI API error — falling back to fixture: %s", exc)`
   - Does local `import streamlit as st` (guards against non-Streamlit test contexts)
   - Checks `hasattr(st, "session_state")` before setting `st.session_state["api_fallback_active"] = True`
   - Assigns `result = _load_fixture()` (does NOT return here — allows logging to fire)
5. Added guarded `_log_analysis_run` call after the try/except block:
   - Wrapped in `try: import st_db as _st_db; _st_db._log_analysis_run(...) except Exception: pass`
   - Passes `run_mode`, `error_type`, `campaign_count`, `latency_ms`, `api_fallback_active` args
6. After logging: `if _fallback_fired: return result` exits the fallback path
7. Success path continues with the existing `logger.info(...)` and `return result`

ValueError from `message.refusal` in `_call_llm()` propagates unhandled — only `openai.OpenAIError` is caught.

### Task 2: test_fixture_validates_against_current_schema

Added `test_fixture_validates_against_current_schema` to `tests/test_llm.py`:
- Calls `llm._load_fixture()`
- Asserts `isinstance(result, AnalysisResult)`
- Asserts `len(result.campaigns) >= 3`

This test guards against fixture drift when schema changes are made in Phase 12 (AI-SPEC §5 Dimension 3). A pre-existing `test_fixture_schema` was left intact — the new test uses the exact name required by the plan's done criteria.

## Verification Results

| Check | Result |
|-------|--------|
| `grep -n "^import openai" llm.py` | line 10: `import openai` |
| `grep -c "except openai.OpenAIError" llm.py` | 1 |
| `grep -c "hasattr(st" llm.py` | 1 |
| `grep -c "_log_analysis_run" llm.py` | 1 |
| `uv run pytest tests/test_llm.py -x -q` | 15 passed |
| Full suite (excluding pre-existing deploy_config failures) | 124 passed, 5 skipped |

## Success Criteria Verification

- [x] `llm.py` has `import openai` added to imports
- [x] `run_analysis()` wraps `_call_llm()` in `try/except openai.OpenAIError` (not except Exception)
- [x] On OpenAI error: `logger.warning` fires, `api_fallback_active=True` set in session state (guarded by hasattr)
- [x] `_log_analysis_run` called via guarded try/except import of st_db after the try/except block
- [x] `ValueError` still propagates unhandled (only `openai.OpenAIError` is caught)
- [x] `tests/test_llm.py` has `test_fixture_validates_against_current_schema` asserting `len(result.campaigns) >= 3`
- [x] `uv run pytest tests/test_llm.py -x -q` exits 0
- [x] Each task committed individually
- [x] No modifications to STATE.md or ROADMAP.md

## Deviations from Plan

None — plan executed exactly as written. The `_log_analysis_run` call pattern followed the `<action>` tag specification (assign result in except branch, log, then conditional return) rather than the simplified PATTERNS.md version (direct return in except branch). This matches the plan's intent to log both success and fallback paths.

## Known Stubs

None — `_log_analysis_run` is guarded by `except Exception: pass` which silently ignores calls when `st_db` does not yet exist. Once `st_db.py` is created in Plan 12-01, the call will succeed. This is intentional design, not a stub.

## Threat Flags

No new security-relevant surface introduced. The changes are:
- Adding `import openai` (already a dependency)
- Adding a guarded `import streamlit as st` inside an except branch
- Adding a guarded `import st_db as _st_db` inside a try/except block

T-12-05 (Tampering — catch only OpenAIError, not Exception) is mitigated as specified.
T-12-SC (no new packages installed) verified — no `uv add` calls made.

## Self-Check: PASSED

- `llm.py` exists and contains `import openai`, `except openai.OpenAIError`, `hasattr(st`, `_log_analysis_run`
- `tests/test_llm.py` contains `test_fixture_validates_against_current_schema`
- Commits `aa3c8dc` and `40b9f3c` exist in git log
