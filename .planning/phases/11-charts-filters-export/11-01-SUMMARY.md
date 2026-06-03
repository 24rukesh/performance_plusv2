---
phase: 11-charts-filters-export
plan: "01"
subsystem: ui
tags: [plotly, fpdf2, pdf, charts, export, dependency]

# Dependency graph
requires:
  - phase: 10-multi-source
    provides: AnalysisResult and CampaignAction Pydantic models consumed by generate_pdf
provides:
  - plotly>=5.20,<7.0 installed and importable in project venv
  - fpdf2>=2.7,<3.0 installed and importable in project venv
  - pdf_report.py module with generate_pdf(result, meta) -> bytes
affects:
  - 11-02 (Charts tab — depends on plotly)
  - 11-04 (PDF export download button — depends on pdf_report.generate_pdf)

# Tech tracking
tech-stack:
  added:
    - plotly 6.7.0 (resolved from >=5.20,<7.0) — interactive charts via Plotly Express
    - fpdf2 2.8.7 (resolved from >=2.7,<3.0) — PDF generation with table() CM API
    - narwhals (transitive, plotly 6.x dep)
    - fonttools (transitive, fpdf2 dep)
    - defusedxml (transitive, fpdf2 dep)
  patterns:
    - TYPE_CHECKING import pattern for AnalysisResult in pure-Python modules (avoids circular import)
    - bytes(pdf.output()) pattern — wraps bytearray to bytes for st.download_button compatibility
    - fpdf2 table() context manager for tabular PDF sections (handles pagination and row fills)

key-files:
  created:
    - pdf_report.py — standalone PDF generation module; no Streamlit import; generate_pdf(result, meta) -> bytes
  modified:
    - pyproject.toml — added plotly>=5.20,<7.0 and fpdf2>=2.7,<3.0 to [project].dependencies
    - uv.lock — regenerated with 4 new packages (plotly, fpdf2, narwhals, fonttools, defusedxml)

key-decisions:
  - "Used bytes(pdf.output()) not bytearray — required for st.download_button compatibility per fpdf2 official Streamlit example"
  - "TYPE_CHECKING import for AnalysisResult prevents circular import at runtime while keeping type hints"
  - "fpdf2 table() context manager chosen over manual cell() loops — handles cell overflow and row pagination automatically"
  - "No streamlit import in pdf_report.py — module must be importable standalone for tests"

patterns-established:
  - "Pure-Python utility module pattern: no Streamlit import, typed return, TYPE_CHECKING for cross-module types"
  - "fpdf2 PDF generation: FPDF() -> add_page() -> set_auto_page_break() -> header cells -> multi_cell summary -> table CM -> bytes(pdf.output())"

requirements-completed: [MGMT-02]

# Metrics
duration: 16min
completed: 2026-06-03
---

# Phase 11 Plan 01: Deps and pdf_report.py Summary

**plotly 6.7.0 and fpdf2 2.8.7 installed via uv; standalone pdf_report.py generates valid PDF bytes from AnalysisResult using fpdf2 table() context manager**

## Performance

- **Duration:** 16 min
- **Started:** 2026-06-03T05:00:00Z
- **Completed:** 2026-06-03T05:16:16Z
- **Tasks:** 2
- **Files modified:** 3 (pyproject.toml, uv.lock, pdf_report.py created)

## Accomplishments

- plotly 6.7.0 and fpdf2 2.8.7 added to pyproject.toml via `uv add`; uv.lock updated with all transitive deps (narwhals, fonttools, defusedxml)
- pdf_report.py created with generate_pdf(result, meta) -> bytes; produces valid PDF (magic bytes %PDF); no Streamlit import
- All 7 verification checks pass: importability, pyproject.toml entries, PDF magic bytes, standalone importability, ruff lint, ruff format

## Task Commits

Each task was committed atomically:

1. **Task 1: Add plotly and fpdf2 dependencies** - `a3cce86` (feat)
2. **Task 2: Create pdf_report.py module** - `6bcd149` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `pdf_report.py` — New standalone PDF generation module; generate_pdf(result, meta) -> bytes; uses fpdf2 table() CM; no Streamlit import; ruff lint+format pass
- `pyproject.toml` — Added `"plotly>=5.20,<7.0"` and `"fpdf2>=2.7,<3.0"` to [project].dependencies
- `uv.lock` — Regenerated; includes plotly 6.7.0, fpdf2 2.8.7, narwhals, fonttools, defusedxml

## Decisions Made

- Used `bytes(pdf.output())` (not `bytearray`) — official fpdf2 Streamlit example requires this wrapping for st.download_button compatibility
- Used `TYPE_CHECKING` import guard for `AnalysisResult` — prevents circular import at runtime while preserving type hints for IDE and static analysis
- Used fpdf2 `table()` context manager (`borders_layout="MINIMAL"`, `cell_fill_mode="ROWS"`) — handles row pagination and alternating fill automatically, simpler than manual cell() loops
- `datetime` import kept with `# noqa: F401` comment — reserved for future date formatting helpers, ruff lint passes with annotation

## Deviations from Plan

None - plan executed exactly as written.

One minor formatting adjustment: ruff format reformatted the initial `table_data` list header declaration from a multi-line `[[...]]` to a single line `[["Campaign ID", ...]]` — this is ruff's canonical style for the configured line-length=100. Verified the reformatted file still passes all verification steps.

## Issues Encountered

None. All steps completed cleanly on first attempt.

## Known Stubs

None. `pdf_report.py` is a complete, functional module. All fields in generate_pdf are wired to actual AnalysisResult data; no placeholder values.

## Threat Flags

No new threat surface beyond what is documented in the plan's threat model (T-11-01-01, T-11-01-02). Both threats accepted per plan. No new endpoints, auth paths, or file writes introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- plotly is installed and importable — unblocks Plan 11-02 (Charts tab with px.scatter and px.bar)
- pdf_report.generate_pdf is ready — unblocks Plan 11-04 (PDF download button in Campaign Actions tab)
- Both Plans 11-02 and 11-04 can proceed in parallel since they depend on different artifacts from this plan

---
*Phase: 11-charts-filters-export*
*Completed: 2026-06-03*
