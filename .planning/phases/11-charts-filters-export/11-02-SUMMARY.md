---
phase: 11-charts-filters-export
plan: 02
subsystem: ui
tags: [streamlit, plotly, charts, tabs, pandas]

# Dependency graph
requires:
  - phase: 10-richer-llm-analysis
    provides: AnalysisResult with source_platforms field; campaign_agg DataFrame; merged_df in session_state
  - phase: 09-multi-source-ingestion
    provides: merged_df with platform and lead_status columns; multi-platform ingest pipeline
provides:
  - 3-tab results layout (Data Preview / Charts / Campaign Actions) in app.py
  - Plotly Express scatter chart (spend vs qualified leads, color=source_platforms)
  - Plotly Express bar chart (action distribution by campaign, color_discrete_map matching ui_helpers.py)
  - Inline qualified_leads_count derivation from merged_df with case-insensitive lead_status filter
  - tab_actions stub ready for Plan 11-03 (filters, comparison, export)
affects: [11-03-filters-comparison, 11-04-export]

# Tech tracking
tech-stack:
  added: [plotly (import plotly.express as px)]
  patterns:
    - chart_df built outside st.tabs() to avoid re-computation on tab switch
    - qualified_leads_count derived inline from merged_df — no data.py changes required
    - Empty source_platforms mapped to "Single source" for legacy single-source DataFrames
    - color_discrete_map keyed on uppercase budget_action strings matching ui_helpers.py constants

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Build chart_df (qual_counts derivation + merge) before st.tabs() call to avoid expensive computation inside tab context managers (RESEARCH.md Pitfall 4)"
  - "Use case-insensitive filter (lead_status.str.lower() == 'qualified') to guard against CRM data casing inconsistencies (RESEARCH.md A1 mitigation)"
  - "Campaign Actions tab contains existing expander loop as stub — Plan 11-03 adds filter/sort/comparison above this loop"
  - "Bar chart color_discrete_map sourced from ui_helpers.py badge color constants as single source of truth"

patterns-established:
  - "Pattern: qualified_leads_count = merged_df.query('lead_status.str.lower() == qualified').groupby(campaign_id).size().reset_index(name=qualified_leads_count)"
  - "Pattern: chart_df constructed via left-merge of campaign_agg + qual_counts + fillna(0)"
  - "Pattern: source_platforms empty string mapped to 'Single source' before chart rendering"

requirements-completed: [VIEW-01]

# Metrics
duration: 9min
completed: 2026-06-03
---

# Phase 11 Plan 02: 3-Tab Layout and Charts Tab Summary

**Restructured app.py results section into st.tabs (Data Preview / Charts / Campaign Actions) with Plotly Express scatter (spend vs qualified leads) and bar (action distribution) charts**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-03T05:18:27Z
- **Completed:** 2026-06-03T05:28:21Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `import plotly.express as px` to top-level imports
- Replaced flat results section with `st.tabs(["Data Preview", "Charts", "Campaign Actions"])` layout
- Charts tab delivers both Plotly Express charts: scatter (spend vs qualified leads, color=source_platforms) and bar (recommended action per campaign)
- qualified_leads_count derived inline from merged_df using case-insensitive lead_status filter — no data.py changes required
- Campaign Actions tab preserves executive summary + per-campaign expander loop as stub for Plan 11-03
- All 124 non-deploy tests pass; 2 pre-existing test_deploy_config.py failures unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Add plotly import and restructure results section into 3-tab layout** - `7c766fc` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `app.py` - Added plotly import; replaced flat results section (lines 365–454) with 3-tab layout; chart_df derivation; scatter + bar charts; preserved Run Analysis gate and token warning gate

## Decisions Made
- chart_df is built before `st.tabs()` call to follow RESEARCH.md Pitfall 4 (all tab code executes on every rerun)
- Used `.str.lower() == 'qualified'` filter instead of exact-case match to guard against CRM data casing inconsistencies (A1 mitigation from RESEARCH.md)
- bar chart `color_discrete_map` uses uppercase keys (`"INCREASE"`, `"PAUSE"`, `"DECREASE"`, `"INSUFFICIENT_DATA"`) matching `.upper()` call on budget_action, with color values matching ui_helpers.py badge colors as single source of truth

## Deviations from Plan

### Minor Acceptance Criterion Discrepancy

The plan acceptance criterion `grep -c "build_exec_summary_html" app.py` states "returns 1 (moved inside tab_actions)". The actual count is 2 because the import line (`from ui_helpers import _badge_html, _pct_html, build_exec_summary_html`) also contains the identifier. This was also the case in the original file before the restructure (import + usage = 2 occurrences). The function usage IS correctly placed inside `with tab_actions:` as intended. No functional impact.

---

**Total deviations:** 0 substantive deviations — plan executed exactly as written. Minor acceptance criterion note above is a pre-existing condition (import + usage = 2), not introduced by this plan.
**Impact on plan:** None.

## Issues Encountered
None — syntax validated clean, all non-deploy tests pass, all acceptance criteria met.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 3-tab layout in place; Plans 11-03 and 11-04 can build on `tab_actions` and `tab_charts` structures
- `with tab_actions:` stub has the existing campaign expander loop — Plan 11-03 adds filter/sort/comparison above this loop
- `chart_df` derivation pattern established for reuse if Plan 11-03 needs qualified_leads_count in filter logic

## Self-Check: PASSED

- `app.py` exists and passes `python3 -c "import ast; ast.parse(open('app.py').read())"` — verified
- Commit `7c766fc` exists — verified via `git rev-parse HEAD`
- All acceptance criteria verified:
  - `import plotly.express as px`: 1 occurrence
  - `st.tabs`: 1 occurrence
  - `tab_preview, tab_charts, tab_actions`: 1 occurrence
  - `px.scatter`: 1 occurrence
  - `px.bar`: 1 occurrence
  - `qualified_leads_count`: 5 occurrences (derivation + chart usage)
  - `lead_status.*lower.*qualified`: 1 occurrence
  - `Single source`: 1 occurrence
  - `tab_actions`: 2 occurrences (assignment + with block)
  - `#09ab3b`: 1 occurrence
  - `build_exec_summary_html`: 2 occurrences (import + usage in tab_actions)
  - `Stitched Dataframe Preview`: 0 occurrences (removed)
  - `Budget Action Results`: 0 occurrences (removed)
- Test suite: 124 passed, 5 skipped, 2 pre-existing failures in test_deploy_config.py

---
*Phase: 11-charts-filters-export*
*Completed: 2026-06-03*
