---
phase: 09-multi-source-ingestion
plan: "02"
subsystem: demo-data
tags: [python, pandas, demo-data, fixtures, multi-currency]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: data_generator.py with generate_web_analytics() and generate_crm_data()
provides:
  - PLATFORM_CURRENCIES dict mapping Google Ads/Meta Ads/LinkedIn Ads/Custom to their default currencies
  - generate_google_ads(), generate_meta_ads(), generate_linkedin_ads(), generate_custom_ads() returning 6-column DataFrames
  - data/google_ads.csv (8 rows, USD), data/meta_ads.csv (6 rows, EUR), data/linkedin_ads.csv (3 rows, GBP), data/custom_ads.csv (3 rows, USD)
  - Idempotent write_csvs() emitting 6 fixture CSVs driven by _FIXTURE_FILE_MAP
  - Phase 9 D-17 smoke-test comment block documenting ingest() integration contract
affects:
  - "09-multi-source-ingestion/09-03 (sidebar Load Demo Data button reads exactly these file paths + PLATFORM_CURRENCIES)"
  - "09-multi-source-ingestion/09-04 (test suite uses these fixture CSVs as test inputs)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_FIXTURE_FILE_MAP list-of-tuples pattern: drives write_csvs() declaratively so adding a new platform requires one line"
    - "Per-platform cost_local in native currency: FX conversion delegated to ingest.py, not the generator"
    - "Multi-platform fan-out via shared session_ids: sess_010 and sess_013 appear in 2+ platforms to exercise ingest() concat path"

key-files:
  created:
    - data/google_ads.csv
    - data/meta_ads.csv
    - data/linkedin_ads.csv
    - data/custom_ads.csv
  modified:
    - data_generator.py

key-decisions:
  - "Added sess_013 to _META_ADS_ROWS (6 rows total) so 2 session_ids (sess_010, sess_013) satisfy the >=2 multi-platform fan-out assertion"
  - "cost_local values in EUR/GBP are derived from USD cost / FX rate (1.08 for EUR, 1.26 for GBP) matching the FX_RATES in ingest.py"
  - "_FIXTURE_FILE_MAP defined at module level (not inside write_csvs) so Plan 09-03 can reference it for the sidebar button"

patterns-established:
  - "Platform fixture pattern: each platform has a _ROWS constant + generator function + entry in _FIXTURE_FILE_MAP"
  - "Smoke-test documentation: if False: guard preserves integration contract as source comments without affecting normal run"

requirements-completed:
  - INGEST-01

# Metrics
duration: 8min
completed: 2026-06-02
---

# Phase 9 Plan 02: Multi-Platform Ad Fixture Generator Summary

**Extended data_generator.py to emit 4 ad-platform CSVs with per-platform currencies (USD/EUR/GBP) and multi-session overlap, confirmed end-to-end with ingest() producing 20 merged rows.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-02T04:12:05Z
- **Completed:** 2026-06-02T04:20:00Z
- **Tasks:** 3
- **Files modified:** 5 (data_generator.py + 4 new CSVs)

## Accomplishments
- Added PLATFORM_CURRENCIES dict and 4 generator functions with the canonical Phase 9 schema (session_id, campaign_id, clicks, impressions, cost_local, conversion_rate)
- Extended write_csvs() via _FIXTURE_FILE_MAP to write 6 fixture CSVs idempotently; verified with re-run
- Smoke-tested all 4 demo CSVs through ingest.ingest() end-to-end: 20 merged rows, 3 currency codes (USD/EUR/GBP), all 4 platform labels present

## Truths Achieved
- data_generator.py produces 4 distinct ad-platform CSVs + 1 CRM CSV, each at the canonical Phase 9 schema
- Each ad-platform CSV has the columns: session_id, campaign_id, clicks, impressions, cost_local, conversion_rate
- Each platform's cost_local is in that platform's default currency (Google Ads -> USD, Meta Ads -> EUR, LinkedIn -> GBP, Custom -> USD)
- Running `python data_generator.py` is idempotent — re-running overwrites without error
- session_id values are shared across platforms (sess_010 and sess_013) so the multi-platform merge exercises the fan-out case
- Existing data/web_analytics.csv stays present and unchanged — legacy load_demo_data() path still works (5 tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add PLATFORM_CURRENCIES + 4 per-platform row lists + generators** - `4bbfcf6` (feat)
2. **Task 2: Extend write_csvs() + generate 4 ad-platform CSVs** - `90835f9` (feat)
3. **Task 3: Smoke-test comment block** - included in `4bbfcf6` (comment block committed with Task 1 write)

## Files Created/Modified
- `data_generator.py` - Added PLATFORM_CURRENCIES, _GOOGLE_ADS_ROWS, _META_ADS_ROWS, _LINKEDIN_ADS_ROWS, _CUSTOM_ADS_ROWS, generate_*_ads() functions, _FIXTURE_FILE_MAP, extended write_csvs(), Phase 9 smoke-test comment block
- `data/google_ads.csv` - 8 rows, cost_local in USD (cmp_b2b_search + cmp_competitor_conquest)
- `data/meta_ads.csv` - 6 rows, cost_local in EUR (cmp_retargeting + cmp_brand_awareness; includes sess_013 for fan-out)
- `data/linkedin_ads.csv` - 3 rows, cost_local in GBP (cmp_linkedin_outbound)
- `data/custom_ads.csv` - 3 rows, cost_local in USD (cmp_retargeting + cmp_brand_awareness; sess_010 + sess_013 overlap with Meta Ads)

## Decisions Made
- Added sess_013 to _META_ADS_ROWS to satisfy the >=2 multi-platform session_id assertion (plan required at least 2 fan-out sessions, only sess_010 existed initially)
- _FIXTURE_FILE_MAP is a module-level constant (not inside write_csvs()) so it can be referenced externally by Plan 09-03's sidebar button
- EUR values use USD / 1.08, GBP values use USD / 1.26 — matching the FX_RATES constants in ingest.py for realistic FX normalization

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added sess_013 to _META_ADS_ROWS to satisfy multi-platform session_id assertion**
- **Found during:** Task 1 verification
- **Issue:** Verify command asserted `len(dupes) >= 2` (at least 2 session_ids in 2+ platforms). Initial implementation had only sess_010 overlapping Meta Ads + Custom Ads.
- **Fix:** Added sess_013 to _META_ADS_ROWS (53.50 USD / 1.08 = 49.54 EUR). sess_013 was already in _CUSTOM_ADS_ROWS.
- **Files modified:** data_generator.py
- **Verification:** Verify command now shows `Multi-platform sessions: ['sess_010', 'sess_013']`
- **Committed in:** 4bbfcf6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary for correctness — the fan-out coverage requirement was clear in the plan spec.

## Issues Encountered
- `python` command not found on this system (macOS uses `python3`); plan verify commands use `python`. Used `python3` equivalents for local verification. The commit scripts themselves use the system python3 path.

## Carry-Forward

### For Plan 09-03 (sidebar Load Demo Data button)
- File paths: `data/google_ads.csv`, `data/meta_ads.csv`, `data/linkedin_ads.csv`, `data/custom_ads.csv`, `data/crm_data.csv`
- Use `PLATFORM_CURRENCIES` from `data_generator` to set the default currency selectbox value for each platform slot
- Session state keys to populate: `google_ads_bytes`, `meta_ads_bytes`, `linkedin_ads_bytes`, `custom_ads_bytes`, `crm_bytes`

### For Plan 09-04 (test suite)
- All 4 CSVs in `data/` are usable as test inputs — pass via `pathlib.Path('data/{platform}.csv').read_bytes()`
- Use `generate_google_ads()`, `generate_meta_ads()`, etc. directly in tests to avoid filesystem dependency
- Multi-platform fan-out case (sess_010 + sess_013 in 2 platforms) should have a dedicated test asserting concat does not raise MergeError

## Next Phase Readiness
- All 4 fixture CSVs are in place and schema-validated
- ingest.py integration confirmed end-to-end (20 merged rows, correct currency codes and platform labels)
- Plan 09-03 sidebar button can immediately reference these file paths

---
*Phase: 09-multi-source-ingestion*
*Completed: 2026-06-02*
