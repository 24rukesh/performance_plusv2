---
phase: 09-multi-source-ingestion
plan: "04"
subsystem: testing
tags: [python, pytest, pandas, ingest, fx-normalization, crm-mapping, column-collision]

# Dependency graph
requires:
  - phase: 09-multi-source-ingestion/09-01
    provides: ingest.py module with SUPPORTED_CURRENCIES, FX_RATES, REQUIRED_CRM_FIELDS, convert_cost(), auto_suggest_crm_columns(), ingest()

provides:
  - tests/test_ingest.py with 24 pytest functions covering every public surface of ingest.py
  - Regression net for INGEST-01, INGEST-02, INGEST-03 contracts in Phases 10-12

affects: [phase-10, phase-11, phase-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_csv_bytes() module-level helper converts list[dict] to CSV bytes for inline test data without temp files"
    - "Module-level row constants (_GOOGLE_ROWS, _META_ROWS, _CRM_STANDARD_ROWS) shared across integration and error-branch tests for DRY fixtures"
    - "Identity field map constant (_IDENTITY_FIELD_MAP) for standard CRM column tests"

key-files:
  created:
    - tests/test_ingest.py
  modified: []

key-decisions:
  - "All 24 tests written as module-level functions (no class wrappers), matching test_data.py style"
  - "Used module-level row constants rather than pytest fixtures to keep test data readable inline"
  - "FX assertions use FX_RATES constants directly (same source as implementation) to protect against rate-value drift while still catching wrong-direction math"
  - "Pre-existing openai-dependent test failures (test_llm.py, test_llm_eval.py, test_ui_helpers.py, test_api.py) documented as environment issues — not regressions from Phase 9"

patterns-established:
  - "_csv_bytes(rows) helper pattern: converts list[dict] to CSV bytes for test inputs without temp file I/O"
  - "Error message assertion pattern: check for both the bad value AND a keyword from the structured error message (e.g., 'XYZ' + 'Supported')"
  - "FX round-trip test: USD → EUR → USD within 1e-9 tolerance verifies bidirectional conversion correctness"

requirements-completed: [INGEST-01, INGEST-02, INGEST-03]

# Metrics
duration: 2min
completed: 2026-06-02
---

# Phase 9 Plan 04: Multi-Source Ingestion Test Suite Summary

**24-function pytest suite for ingest.py covering constants, FX maths, happy-path integration, error branches, CRM field mapping, column collision defence, and edge cases — 100% pass rate**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-02T04:19:49Z
- **Completed:** 2026-06-02T04:22:12Z
- **Tasks:** 4 (3 code tasks + 1 regression check)
- **Files modified:** 1 created

## Accomplishments

- 24 pytest test functions covering every public surface of ingest.py (SUPPORTED_CURRENCIES, FX_RATES, REQUIRED_CRM_FIELDS, convert_cost, auto_suggest_crm_columns, ingest)
- FX normalisation validated end-to-end: identity conversion, USD/EUR round-trip, reporting currency variance, platform currency validation, reporting currency validation
- Error branches exercised: unsupported platform currency, unsupported reporting currency, duplicate CRM session_id (pd.errors.MergeError), incomplete field map, field map referencing missing column, empty platforms list, all-None bytes
- Column collision defence verified: two platforms with identical non-key column both get source-prefixed and no _x/_y suffixes survive
- CRM field mapping with non-standard column names verified: canonical field names appear in output, original column names absent
- Orphaned session drop verified: inner merge correctly drops ad rows with no CRM match

## Task Commits

Each task was committed atomically:

1. **Tasks 1-3: Create tests/test_ingest.py (all 24 tests)** - `50d22c2` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `/Users/rukesh/Documents/Dev/performance_plus/tests/test_ingest.py` - 24 pytest functions covering all public surfaces of ingest.py; 487 lines

## Decisions Made

- Used module-level row constants (_GOOGLE_ROWS, _META_ROWS, _CRM_STANDARD_ROWS, _IDENTITY_FIELD_MAP) instead of pytest fixtures — keeps test data visible inline and avoids conftest.py complexity for a single-module suite
- FX assertions reference FX_RATES constants directly (same dict the implementation uses) so tests fail if the dict values change unexpectedly while still catching wrong-direction math errors
- Pre-existing environment failures (test_llm.py, test_ui_helpers.py, test_api.py, test_phase7_landing.py) require `openai` package not installed in the system Python 3.13 environment; these are not regressions from this plan

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. All 24 tests passed on first run. The pre-existing `ModuleNotFoundError: No module named 'openai'` in test_llm.py, test_llm_eval.py, test_ui_helpers.py, and test_api.py is an environment issue (openai not installed in the system Python 3.13) that predates this plan.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Regression net is in place: when Phase 10 extends `compute_campaign_agg` or `run_analysis`, run `pytest tests/test_ingest.py` to confirm the underlying merged DataFrame contract (column names, FX values, CRM field names, source prefixes) is preserved
- If `convert_cost` is modified (e.g., to use live FX rates), the round-trip test and reporting-currency variance test will catch regressions immediately
- If REQUIRED_CRM_FIELDS or SUPPORTED_CURRENCIES lists are reordered or extended, the exact-list tests will fail, forcing intentional update of the constants test

## Self-Check

- `/Users/rukesh/Documents/Dev/performance_plus/tests/test_ingest.py` — FOUND
- Commit `50d22c2` — FOUND (git rev-parse confirmed)
- 24 tests, all passing: `pytest tests/test_ingest.py` → 24 passed in 0.37s

## Self-Check: PASSED

---
*Phase: 09-multi-source-ingestion*
*Completed: 2026-06-02*
