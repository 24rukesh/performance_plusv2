---
phase: 07-landing-page-ui-polish
plan: 01
subsystem: ui
tags: [streamlit, html, st.expander, ui_helpers, branded-header]

# Dependency graph
requires:
  - phase: 06-fastapi-service
    provides: "ui_helpers.py with _badge_html, _pct_html, build_results_table_html, build_exec_summary_html"
provides:
  - "BRANDED_HEADER_HTML constant in app.py with product name, tagline, and Back-to-site link"
  - "st.expander per-campaign results layout replacing HTML results table"
  - "Updated app.py import: _badge_html, _pct_html, build_exec_summary_html (build_results_table_html dropped from import)"
affects: [07-landing-page-ui-polish, 08-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BRANDED_HEADER_HTML module-level constant pattern for static HTML in Streamlit"
    - "st.expander per-row results loop with badge HTML inside body (not label)"
    - "unsafe_allow_html=True only for developer-controlled or Pydantic-validated HTML"

key-files:
  created: []
  modified:
    - app.py

key-decisions:
  - "BRANDED_HEADER_HTML placed after load_dotenv() and before st.set_page_config() in source order (still module-level), preserving st.set_page_config as first Streamlit call"
  - "build_results_table_html retained in ui_helpers.py — only removed from app.py import to avoid F401; tests/test_ui_helpers.py depends on it"
  - "st.expander label uses plain-text (Pitfall 2: labels do not render HTML); badge HTML rendered inside expander body via st.markdown"

patterns-established:
  - "Pattern: import update strips unused symbol from app.py without deleting the function from its source module (test dependency preserved)"
  - "Pattern: pct_display computed as +N% / N% to give readable plain-text in expander label"

requirements-completed: [UI-03, UI-04, UI-05]

# Metrics
duration: 2min
completed: 2026-06-01
---

# Phase 7 Plan 01: Landing Page UI Polish — Streamlit Branded Header + Expander Results Summary

**Streamlit app branded with BRANDED_HEADER_HTML constant (product name, tagline, Back-to-site link) and campaign results refactored from HTML table to st.expander loop showing reasoning inline**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-01T10:52:24Z
- **Completed:** 2026-06-01T10:54:28Z
- **Tasks:** 2
- **Files modified:** 1 (app.py only)

## Accomplishments
- Replaced `st.title("Performance Plus")` + `st.write("Autonomous Semantic Attribution Engine")` with `st.markdown(BRANDED_HEADER_HTML, unsafe_allow_html=True)` — product name at 22px/600 weight, tagline at 14px/400 weight muted, Back-to-site anchor at 13px with href="/"
- Updated `from ui_helpers import` line to add `_badge_html` and `_pct_html`, drop `build_results_table_html` (eliminating potential ruff F401)
- Replaced dense HTML results table with `for c in result.campaigns:` loop using `st.expander` — badge HTML rendered inside body, reasoning via `st.write`, confidence/sessions via `st.caption`

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace st.title + st.write with branded header** - `3613d08` (feat)
2. **Task 2: Replace results table with st.expander loop + fix import** - `55bd5d0` (feat)

**Plan metadata:** committed below (docs)

## Files Created/Modified
- `/Users/rukesh/Documents/Dev/performance_plus/app.py` - Added BRANDED_HEADER_HTML constant, replaced st.title/st.write, updated ui_helpers import, replaced build_results_table_html call with st.expander loop

## Decisions Made
- `BRANDED_HEADER_HTML` constant is placed after `load_dotenv()` and before `st.set_page_config(...)` in source order — it is module-level Python (no Streamlit API call), so `st.set_page_config` remains the first actual Streamlit call, satisfying Pitfall 6
- `build_results_table_html` was removed from the `app.py` import line but deliberately kept in `ui_helpers.py` because `tests/test_ui_helpers.py` (lines 4, 72, 92) imports and asserts against it
- Expander label uses plain-text `f"{c.campaign_id} — {c.budget_action.upper()} {pct_display}"` per Pitfall 2 (st.expander labels strip HTML)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- app.py is ready; Streamlit shows branded header and expandable campaign results
- ui_helpers.py is unchanged and all tests pass (46 passed, 5 skipped)
- Phase 07-02 (Next.js landing page scaffold) and 07-03/07-04 can proceed independently

---
*Phase: 07-landing-page-ui-polish*
*Completed: 2026-06-01*
