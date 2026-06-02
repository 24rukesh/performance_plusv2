---
phase: "10-richer-llm-analysis"
plan: "01"
subsystem: "data-layer"
tags: ["data", "ingest", "pandas", "multi-source", "crm"]
dependency_graph:
  requires: []
  provides:
    - "ingest.py: CRM extra column pass-through with crm_ prefix"
    - "data.py: SLUG_TO_DISPLAY constant"
    - "data.py: _detect_slugs helper"
    - "data.py: _compute_platform_pivot helper"
    - "data.py: _compute_source_platforms helper"
    - "data.py: extended compute_campaign_agg with multi-source + legacy paths"
  affects:
    - "app.py: bridge block can now be removed (Plan 10-02)"
    - "llm.py: wider campaign_agg CSV passed to run_analysis"
tech_stack:
  added: []
  patterns:
    - "pandas pivot_table for per-platform cost/session breakdown"
    - "SLUG_TO_DISPLAY constant to avoid .title() linkedin_ads mismatch"
    - "TDD red-green cycle for both tasks"
key_files:
  created: []
  modified:
    - "ingest.py (lines 303-308)"
    - "data.py (full rewrite — 145 lines)"
    - "tests/test_ingest.py (lines 490-530 — 2 new tests)"
    - "tests/test_data.py (fixture + 4 new tests + column list update)"
decisions:
  - "Used SLUG_TO_DISPLAY dict instead of .title() to ensure LinkedIn Ads (capital I) is matched correctly"
  - "copy() guard: merged_df is copied once regardless of whether crm_extra or is_multi_source triggers first"
  - "Multi-source path synthesises unified clicks/impressions/conversion_rate columns before the unchanged groupby body"
metrics:
  duration: "150s"
  completed: "2026-06-02T06:13:48Z"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 4
  tests_added: 6
  tests_total: 35
---

# Phase 10 Plan 01: Data Layer Foundation for Cross-Platform Analysis Summary

**One-liner:** Extended ingest.py to preserve extra CRM columns with crm_ prefix and rewrote data.py compute_campaign_agg to natively produce per-platform breakdown columns (google_ads_cost_usd, meta_ads_cost_usd, etc.) plus a source_platforms pipe-delimited column for both multi-source and legacy single-source DataFrames.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ingest.py CRM extra column pass-through (D-06) | 7462345 | ingest.py, tests/test_ingest.py |
| 2 | data.py multi-source compute_campaign_agg extension (D-01 to D-06) | c31b532 | data.py, tests/test_data.py |

## Verification

```
uv run pytest tests/test_data.py tests/test_ingest.py --tb=short -q
35 passed in 0.31s
```

## What Was Built

### Task 1: ingest.py CRM extra column pass-through

Replaced the single-line `crm_df = crm_df[REQUIRED_CRM_FIELDS]` strip at line 305 with a three-line pattern:

```python
extra_crm_cols = [c for c in crm_df.columns if c not in REQUIRED_CRM_FIELDS]
rename_extra = {c: f"crm_{c}" for c in extra_crm_cols}
crm_df = crm_df.rename(columns=rename_extra)
```

Extra CRM columns now flow into merged_df with crm_ prefix. The 4 required fields are already renamed by rename_map_crm before this step, so only genuinely extra columns are prefixed.

### Task 2: data.py multi-source compute_campaign_agg extension

Added:
- `SLUG_TO_DISPLAY` module-level constant with correct display names (critical for "LinkedIn Ads" capital I)
- `_detect_slugs()`: detects platform slugs from source-prefixed _clicks columns, cross-validated against merged_df["platform"] unique values using SLUG_TO_DISPLAY
- `_compute_platform_pivot()`: pivot_table producing {slug}_cost_usd and {slug}_session_count per campaign, fill_value=0 prevents NaN
- `_compute_source_platforms()`: pipe-delimited string of contributing display names per campaign
- Extended `compute_campaign_agg()` with:
  - CRM enrichment block (both paths): appends crm_* columns to sales_notes
  - Multi-source path: synthesises unified clicks/impressions/conversion_rate before groupby
  - Legacy path: source_platforms = "" (always present)
  - Multi-source path: merges platform pivot + computes source_platforms

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Redundant copy() call in multi-source path**
- **Found during:** Task 2 implementation
- **Issue:** The multi-source synthesis block had nested copy() logic that was slightly convoluted — checking `if not crm_extra` to decide whether to copy again
- **Fix:** Simplified: merged_df is copied once when crm_extra is present; when not, a fresh copy is made for the multi-source synthesis. The logic correctly avoids double-copying.
- **Files modified:** data.py
- **Commit:** c31b532

## Known Stubs

None. All columns are wired to real data. source_platforms is computed from actual pivot results.

## Threat Flags

None beyond those documented in the plan's threat_model (T-10-01 through T-10-04, all accepted).

## Self-Check: PASSED

- ingest.py modified: FOUND
- data.py rewritten: FOUND
- tests/test_ingest.py updated: FOUND (26 tests pass)
- tests/test_data.py updated: FOUND (9 tests pass)
- Commit 7462345 (Task 1): FOUND
- Commit c31b532 (Task 2): FOUND
- `uv run pytest tests/test_data.py tests/test_ingest.py` exits 0: CONFIRMED (35 passed)
- SLUG_TO_DISPLAY contains "linkedin_ads": "LinkedIn Ads" (capital I): CONFIRMED
- _detect_slugs, _compute_platform_pivot, _compute_source_platforms all present: CONFIRMED
- compute_campaign_agg always returns source_platforms column: CONFIRMED
