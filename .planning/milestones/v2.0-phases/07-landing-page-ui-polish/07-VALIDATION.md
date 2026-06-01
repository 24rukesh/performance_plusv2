---
phase: 7
slug: landing-page-ui-polish
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-01
---

# Phase 7 — Validation Strategy

> Per-phase validation contract: test coverage, gap analysis, and sign-off.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8+ (Python structural/static analysis tests) |
| **Config file** | `pyproject.toml` (project root) |
| **Phase 7 file** | `tests/test_phase7_landing.py` (35 tests) |
| **Quick run command** | `uv run pytest tests/test_phase7_landing.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~0.7s (full suite), ~0.65s (phase file only) |
| **Baseline** | 46 passed, 5 skipped (pre-phase) |
| **After phase** | 81 passed, 5 skipped |

**Note on Next.js components (LAND-*):** No jest/vitest is installed. All landing component tests are structural/static-analysis pytest tests — they verify file existence, content patterns, security assertions, and cross-stack hex parity using `pathlib.Path` reads and regex. TypeScript correctness is verified via `npx tsc --noEmit` (Plan 02/03) and `npm run build` (Plan 04) acceptance gates.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_phase7_landing.py -q`
- **After every plan wave:** `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-T1 | 01 | 1 | UI-03 | T-07-01, T-07-02 | `BRANDED_HEADER_HTML` is static constant, no user input | structural | `uv run pytest tests/test_phase7_landing.py::test_app_defines_BRANDED_HEADER_HTML_constant tests/test_phase7_landing.py::test_BRANDED_HEADER_HTML_contains_required_strings tests/test_phase7_landing.py::test_app_calls_st_markdown_with_BRANDED_HEADER_HTML tests/test_phase7_landing.py::test_old_st_title_and_st_write_removed -q` | ✅ | ✅ green |
| 07-01-T2 | 01 | 1 | UI-04 | T-07-02, T-07-03 | Badge HTML via Literal enum only; `st.write()` auto-escapes reasoning | structural | `uv run pytest tests/test_phase7_landing.py::test_app_has_for_c_in_result_campaigns tests/test_phase7_landing.py::test_app_has_st_expander tests/test_phase7_landing.py::test_app_renders_semantic_reasoning_via_st_write tests/test_phase7_landing.py::test_app_has_confidence_caption -q` | ✅ | ✅ green |
| 07-01-T2 | 01 | 1 | UI-05 | — | Import line excludes unused symbol; function still available for tests | structural | `uv run pytest tests/test_phase7_landing.py::test_app_imports_badge_html_and_pct_html tests/test_phase7_landing.py::test_app_does_not_import_build_results_table_html tests/test_phase7_landing.py::test_build_results_table_html_still_importable_from_ui_helpers tests/test_phase7_landing.py::test_build_results_table_html_runtime_importable -q` | ✅ | ✅ green |
| 07-02-T1 | 02 | 1 | LAND-01 | T-07-05, T-07-07, T-07-08 | @theme tokens in CSS only (no tailwind.config.ts); env var falls back to same-origin | structural | `uv run pytest tests/test_phase7_landing.py::test_globals_css_exists_and_has_theme_block tests/test_phase7_landing.py::test_globals_css_brand_badge_hex_tokens tests/test_phase7_landing.py::test_layout_tsx_loads_ibm_plex_sans tests/test_phase7_landing.py::test_globals_css_fadeslide_in_keyframe -q` | ✅ | ✅ green |
| 07-02-T2 | 02 | 1 | LAND-03 | — | Cross-stack hex parity LOCKED; any drift breaks badge rendering | structural (parity) | `uv run pytest tests/test_phase7_landing.py::test_badge_tokens_ts_increase_bg_is_09ab3b tests/test_phase7_landing.py::test_badge_tokens_ts_pause_bg_is_ff2b2b tests/test_phase7_landing.py::test_badge_tokens_ts_decrease_bg_is_faca2b tests/test_phase7_landing.py::test_badge_tokens_ts_insufficient_data_bg_is_808495 tests/test_phase7_landing.py::test_badge_tokens_ts_parity_with_ui_helpers tests/test_phase7_landing.py::test_badge_tokens_pct_color_values -q` | ✅ | ✅ green |
| 07-03-T1 | 03 | 1 | LAND-02 | T-07-07, T-07-10, T-07-11, T-07-12 | WaitlistForm never echoes `res.json()`; `rel="noopener noreferrer"` present | structural + security | `uv run pytest tests/test_phase7_landing.py::test_waitlist_form_tsx_exists tests/test_phase7_landing.py::test_hero_section_tsx_exists tests/test_phase7_landing.py::test_how_it_works_section_tsx_exists tests/test_phase7_landing.py::test_waitlist_form_does_not_use_res_json tests/test_phase7_landing.py::test_hero_section_has_rel_noopener_noreferrer tests/test_phase7_landing.py::test_landing_env_example_contains_api_base_url tests/test_phase7_landing.py::test_landing_gitignore_covers_env_files -q` | ✅ | ✅ green |
| 07-04-T1 | 04 | 1 | LAND-04 | T-07-09, T-07-15, T-07-17, T-07-18 | `observer.disconnect()` on first intersection + useEffect cleanup; no `dangerouslySetInnerHTML` | structural + security | `uv run pytest tests/test_phase7_landing.py::test_demo_animation_tsx_exists tests/test_phase7_landing.py::test_demo_animation_has_observer_disconnect tests/test_phase7_landing.py::test_demo_animation_has_useeffect_cleanup tests/test_phase7_landing.py::test_features_section_tsx_exists tests/test_phase7_landing.py::test_footer_tsx_exists tests/test_phase7_landing.py::test_no_dangerously_set_inner_html_in_landing_components -q` | ✅ | ✅ green |

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.
- `tests/test_phase7_landing.py` — 35 structural tests generated during validate-phase (2026-06-01)
- No new framework installation required (pytest already present)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Next.js TypeScript compilation clean | LAND-01/02/03/04 | No jest/vitest installed; tsc is build-time only | `cd landing && npx tsc --noEmit` → exits 0 |
| Next.js production build succeeds | LAND-04 | Build output not deterministically testable from pytest | `cd landing && npm run build` → exits 0; `landing/.next/` exists |
| Streamlit branded header renders visually | UI-03 | Requires browser + Streamlit runtime | Start app, verify `⚡ Performance Plus` header, tagline, and `← Back to site` link render at page top |
| st.expander interaction works end-to-end | UI-04 | Requires Streamlit runtime + LLM analysis result | Run analysis, click expander, verify badge + reasoning + confidence caption appear inline |
| Landing page renders and WaitlistForm submits | LAND-02 | Requires Next.js dev server + FastAPI backend | `cd landing && npm run dev`, open localhost:3000, submit email, verify 5-state form transitions |
| DemoAnimation fadeSlideIn scroll trigger | LAND-04 | Requires browser + IntersectionObserver | Open landing page, scroll to Demo section, verify cards animate in on first intersection |

---

## Validation Audit Trail

### Initial Audit — 2026-06-01

| Metric | Count |
|--------|-------|
| Requirements total | 7 (UI-03, UI-04, UI-05, LAND-01, LAND-02, LAND-03, LAND-04) |
| MISSING gaps found | 6 |
| PARTIAL gaps found | 1 |
| Tests generated | 35 |
| Gaps resolved | 7/7 |
| Escalated to manual-only | 0 |
| Baseline preserved | ✅ (46 passed, 5 skipped → unchanged) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 1s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-01
