---
phase: 09-multi-source-ingestion
plan: "03"
subsystem: ui
tags: [python, streamlit, multi-upload, session-state, fx-normalization, ingest]

# Dependency graph
requires:
  - phase: 09-multi-source-ingestion
    provides: "09-01: ingest.py with SUPPORTED_CURRENCIES, REQUIRED_CRM_FIELDS, auto_suggest_crm_columns, ingest()"
  - phase: 09-multi-source-ingestion
    provides: "09-02: data_generator.py with PLATFORM_CURRENCIES and 4 ad-platform + CRM demo CSVs"
provides:
  - "Multi-source upload UI: 4-platform grid with per-platform currency selectors"
  - "CRM uploader with field-mapping UI (auto-suggest, explicit Confirm Mapping, extra pass-through columns)"
  - "Sidebar Reporting Currency selectbox backed by SUPPORTED_CURRENCIES from ingest.py"
  - "Sidebar Load Demo Data button pre-filling all 5 session_state bytes keys from disk fixtures"
  - "Run Analysis gate gating on >=1 ad bytes + crm_bytes + crm_field_map"
  - "ingest() call chain wired: ingest() -> compute_campaign_agg() -> run_analysis()"
  - "ValueError and MergeError error handling with user-facing copy per UI-SPEC"
affects: [phase-10, phase-11, phase-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bytes-copy pattern: file_uploader.getvalue() stored in session_state bytes key (not UploadedFile object)"
    - "_PLATFORMS constant: 4-tuple list defining display name, slug, bytes key, uploader key, currency key, default currency"
    - "Run Analysis gate: _any_ad_bytes + crm_bytes + crm_field_map all populated before enabling ingest call"
    - "ingest() called once per cache miss (merged_df is None) to avoid redundant ingestion on Streamlit reruns"
    - "compute_campaign_agg compat bridge: sums source-prefixed *_clicks/*_impressions, averages *_conversion_rate into unprefixed names"

key-files:
  created: []
  modified:
    - app.py

key-decisions:
  - "load_demo_data import removed from app.py — sidebar Load Demo Data button reads bytes directly via pathlib; legacy function remains in data.py for test suite"
  - "compute_campaign_agg compat bridge added in app.py (sums google_ads_clicks + meta_ads_clicks etc. into clicks) — Phase 10 will extend compute_campaign_agg natively and remove this bridge"
  - "Confirm Mapping button uses default (secondary) style per UI-SPEC — primary accent reserved for Run Analysis + Load Demo Data"
  - "Custom platform name from text_input falls back to 'Custom' label when blank"

patterns-established:
  - "Bytes-copy pattern: always store .getvalue() result in session_state, never the UploadedFile object"
  - "Gate pattern: compute gate bool before rendering gate-dependent UI; show info with missing items list when not ready"

requirements-completed: [INGEST-01, INGEST-02]

# Metrics
duration: ~90min (including manual smoke test)
completed: 2026-06-02
---

# Phase 9 Plan 03: Multi-Source Upload UI Summary

**Streamlit app.py rewritten with 4-platform CSV upload grid, CRM field-mapping UI, sidebar Reporting Currency + Load Demo Data, and ingest() call chain wired end-to-end — smoke test approved, Run Analysis works with demo data**

## Performance

- **Duration:** ~90 min (including manual smoke test roundtrip)
- **Started:** 2026-06-02
- **Completed:** 2026-06-02
- **Tasks:** 4 (Tasks 1-3 auto, Task 4 human-verify — approved)
- **Files modified:** 1 (app.py), plus post-task bridge fix to app.py

## Accomplishments

- Replaced single-CSV upload flow with 4-platform grid (Google Ads top-left, LinkedIn Ads bottom-left, Meta Ads top-right, Custom bottom-right) with per-platform currency selectors in 3:1 column ratio
- Added CRM uploader with difflib-based auto-suggest field mapping, 4 required-field selectboxes, optional pass-through multiselect, and Confirm Mapping button writing to session_state
- Sidebar extended with Reporting Currency selectbox (8 SUPPORTED_CURRENCIES, USD default) and Demo Data subsection with Load Demo Data primary button reading 5 fixture files via pathlib
- Run Analysis gate enforces all 3 preconditions (>=1 ad bytes, crm_bytes, crm_field_map); shows missing-items info copy when incomplete
- ingest() called once per merged_df cache miss; ValueError (unsupported currency, column collision) and MergeError (duplicate session_id) all handled with curated user-facing copy
- Manual smoke test: all 9 verification steps passed; Run Analysis end-to-end succeeded with demo data

## Task Commits

1. **Task 1: Session_state init, sidebar Reporting Currency + Demo Data, import ingest constants** - `b8d5b9a` (feat)
2. **Task 2: 4-platform upload grid + CRM uploader + CRM field-mapping UI** - `b8d5b9a` (feat)
3. **Task 3: Run Analysis gate, ingest() wiring, error handling, preserve analysis flow** - `b8d5b9a` (feat)
4. **Task 4: Manual UI smoke test** - approved (no commit — human verification)
5. **Bridge fix: compute_campaign_agg compat** - `5bbdc71` (fix — post-task deviation)

_Note: Tasks 1-3 were executed atomically in a single commit per the plan's single-file scope._

## Files Created/Modified

- `app.py` — Rewrote upload section: added _PLATFORMS constant, _render_platform_slot() helper, 4-platform grid, CRM uploader + mapping UI, sidebar Reporting Currency + Demo Data, Run Analysis gate, ingest() call, error handling, dynamic Sources caption, removed load_demo_data import, removed main-area Load Demo Data button. Post-task: bridge summing source-prefixed numeric columns added before compute_campaign_agg call.

## Decisions Made

- `load_demo_data` import dropped from app.py — sidebar button reads bytes directly via `pathlib.Path(__file__).parent / "data"` hardcoded path; function stays in data.py for test coverage
- Confirm Mapping uses default (secondary) button style per UI-SPEC — primary accent reserved for Run Analysis and Load Demo Data only
- compute_campaign_agg compat bridge committed separately (`5bbdc71`) after smoke test revealed source-prefixed columns (e.g. `google_ads_clicks`) were not being aggregated by the unchanged data.py function; bridge sums `*_clicks` and `*_impressions`, averages `*_conversion_rate` into unprefixed names before calling compute_campaign_agg
- Phase 10 will extend compute_campaign_agg natively and remove the bridge

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] compute_campaign_agg compat bridge added post-smoke-test**
- **Found during:** Task 4 (manual UI smoke test — Run Analysis end-to-end)
- **Issue:** After Plan 09-01's ingest() renamed all numeric columns with source prefixes (e.g. `google_ads_clicks`, `meta_ads_clicks`), the unchanged `compute_campaign_agg()` in data.py expected unprefixed column names (`clicks`, `impressions`, `conversion_rate`). The merged DataFrame lacked these columns, causing KeyError or silent NaN aggregation in the analysis pipeline.
- **Fix:** Added a bridge block in app.py immediately before the `compute_campaign_agg(merged_df)` call. The bridge sums all `*_clicks` and `*_impressions` columns (any column ending in `_clicks` / `_impressions`) into `clicks` / `impressions`, and averages all `*_conversion_rate` columns into `conversion_rate`. Existing unprefixed columns (e.g. from a single-source run) are preserved if already present.
- **Files modified:** app.py
- **Verification:** Run Analysis completed end-to-end with demo data (4 platforms merged); Budget Action Results rendered correctly
- **Committed in:** `5bbdc71` (separate fix commit after Task 3 feat commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Fix necessary for correctness. Scope is minimal — bridge is a 10-line block in app.py. Phase 10 owns the permanent solution in data.py.

## Issues Encountered

None beyond the deviation documented above. All three auto-verify commands (py_compile, AST checks) passed after each task. Test suite (test_data.py, test_llm.py, test_ui_helpers.py, test_api.py) had zero regressions — compute_campaign_agg signature is unchanged so existing tests continue to pass.

## User Setup Required

None — no external service configuration required. OPENAI_API_KEY is passed via sidebar input or .env; demo data files are generated by data_generator.py (already committed in 09-02).

## Known Stubs

None. All session_state keys are wired to real data sources (file uploads or fixture CSVs). The analysis pipeline produces real LLM output when an API key is present (or uses DEMO_MODE=1 mock path).

## Threat Flags

No new unsafe_allow_html call sites introduced. custom_platform_name flows only into st.caption and the `platform` column in st.dataframe (both escaped by Streamlit). T-09-12 through T-09-19 mitigations confirmed present per plan threat model.

## Next Phase Readiness

**Phase 10 carry-forward (mandatory):**

`compute_campaign_agg` in data.py must be extended to natively aggregate source-prefixed numeric columns (`google_ads_clicks`, `meta_ads_clicks`, `linkedin_ads_clicks`, `custom_ads_clicks`, etc.) into the per-campaign `clicks`, `impressions`, and `conversion_rate` aggregates. Once that extension lands, the bridge block added in `app.py` (commit `5bbdc71`) must be removed.

The `merged_df["platform"]` column and all source-prefixed numeric columns are now available in the merged DataFrame — Phase 10 can use them to attribute performance metrics per platform in the LLM prompt and in the CampaignAction response schema.

**Phase 10 is unblocked.** Multi-source ingestion (INGEST-01, INGEST-02) is fully live. The Run Analysis end-to-end path works correctly with demo data.

---
*Phase: 09-multi-source-ingestion*
*Completed: 2026-06-02*
