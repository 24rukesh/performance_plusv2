---
phase: "10-richer-llm-analysis"
plan: "04"
subsystem: "tests"
tags: ["test", "multi-source", "schema", "tiktoken", "source_platforms"]
dependency_graph:
  requires: ["10-01", "10-02"]
  provides:
    - "tests/test_data.py: multi-source agg breakdown column assertions"
    - "tests/test_data.py: source_platforms column tests"
    - "tests/test_llm.py: CampaignAction schema required[] tests"
    - "tests/test_llm.py: count_prompt_tokens tests"
    - "tests/test_llm.py: SYSTEM_PROMPT rule tests"
  affects:
    - "Regression protection for Phase 10 multi-source data pipeline"
tech_stack:
  added: []
  patterns: ["pytest.approx for float comparisons", "DataFrame fixture pattern"]
key-files:
  modified:
    - "tests/test_data.py"
    - "tests/test_llm.py"
decisions:
  - "Tests absorbed into Plans 10-02 and 10-03 during incremental development; all tests verified passing in final wave-2 run"
metrics:
  duration: "< 5 minutes"
  completed: "2026-06-02"
---

# Phase 10 Plan 04: Multi-Source Agg, Schema, and Tiktoken Unit Tests Summary

Unit test coverage for all Phase 10 behaviors: multi-source platform breakdown columns, source_platforms column, CampaignAction JSON Schema required[] enforcement, and tiktoken-based count_prompt_tokens helper.

## What Was Done

This plan delivered unit test coverage for the data and LLM layer changes introduced in Plans 10-01 and 10-02. The test functions were already written and committed by those prior plans during incremental development. This plan's role was to verify all tests pass against the complete implementation.

### tests/test_data.py (9 tests total)

**Updated existing test:**
- `test_compute_campaign_agg_returns_five_campaigns` — column list assertion updated to include `"source_platforms"` as the 9th column

**New helper function:**
- `_multi_source_merged_df()` — 3-row DataFrame fixture with `cmp_a` (Google Ads session s1 + Meta Ads session s2) and `cmp_b` (Google Ads session s3), including all platform-prefixed columns

**New test functions:**
- `test_compute_campaign_agg_multi_source_breakdown_columns` — asserts 4 breakdown columns present; validates `cmp_a` google_ads_cost_usd==10.0, meta_ads_cost_usd==5.0, session counts==1 each using pytest.approx
- `test_compute_campaign_agg_source_platforms_column` — asserts `source_platforms` column present; `cmp_a` contains both "Google Ads" and "Meta Ads"; `cmp_b` == "Google Ads"
- `test_compute_campaign_agg_legacy_path_unchanged` — uses `load_demo_data()` (no platform column), asserts `source_platforms` present and all values == ""
- `test_compute_campaign_agg_crm_extra_cols_in_sales_notes` — asserts `crm_-prefixed` extra columns are appended to sales_notes string (D-06 behavior)

### tests/test_llm.py (14 tests total, 4 new)

**New test functions:**
- `test_source_platforms_in_schema_required` — verifies `"source_platforms"` in `CampaignAction.model_json_schema()["required"]`; type == "array"; items type == "string"
- `test_count_prompt_tokens_returns_int` — verifies `count_prompt_tokens(_minimal_agg_df())` returns `isinstance(count, int)` and `count > 0`
- `test_count_prompt_tokens_scales_with_data` — verifies larger DataFrame produces higher token count than single-row DataFrame
- `test_system_prompt_contains_cross_platform_rule` — verifies `"Cross-platform"` and `"source_platforms"` both present in `SYSTEM_PROMPT`

## Verification Results

Full test suite run:
```
uv run pytest tests/test_data.py tests/test_llm.py tests/test_ingest.py --tb=short -q
49 passed in 1.05s
```

Tiktoken encoding verification:
```
uv run python -c "from llm import count_prompt_tokens; import pandas as pd; df = pd.DataFrame([{'campaign_id': 'c', 'total_clicks': 1}]); print(count_prompt_tokens(df))"
286
```

Per-file breakdown:
- `test_data.py`: 9 tests (5 original + 4 new)
- `test_llm.py`: 14 tests (10 original + 4 new)
- `test_ingest.py`: 26 tests (unchanged)
- Total: 49 tests, 0 failures

## Deviations from Plan

### Delivery context note

The test functions specified in this plan were written incrementally during Plans 10-02 and 10-03 rather than in a separate 10-04 commit. The implementation order was:
- Plan 10-02 committed `test_campaign_action_schema_valid`, `_make_valid_analysis_result`, and the new `test_source_platforms_in_schema_required`, `test_count_prompt_tokens_*`, and `test_system_prompt_*` functions alongside the llm.py changes
- Plan 10-01 committed the `_multi_source_merged_df` fixture and data.py tests alongside the data.py implementation

This is a GREEN-phase execution (Wave 2) — the tests were already in place and passing against the complete Phase 10 implementations. No new code was written in this plan execution; verification confirmed all success criteria are met.

## Known Stubs

None. All test assertions exercise real implementations.

## Self-Check: PASSED

- tests/test_data.py: FOUND (9 tests, all pass)
- tests/test_llm.py: FOUND (14 tests, all pass)
- test_source_platforms_in_schema_required: FOUND and PASSED
- test_count_prompt_tokens_returns_int: FOUND and PASSED
- test_count_prompt_tokens_scales_with_data: FOUND and PASSED
- test_system_prompt_contains_cross_platform_rule: FOUND and PASSED
- test_compute_campaign_agg_multi_source_breakdown_columns: FOUND and PASSED
- test_compute_campaign_agg_source_platforms_column: FOUND and PASSED
- test_compute_campaign_agg_legacy_path_unchanged: FOUND and PASSED
- Full suite (49 tests): PASSED
