"""
Comprehensive pytest suite for ingest.py public surface.

Covers:
- Module-level constants: SUPPORTED_CURRENCIES, FX_RATES, REQUIRED_CRM_FIELDS
- Helper functions: convert_cost(), auto_suggest_crm_columns()
- Main pipeline: ingest() — happy path, FX normalisation, orphaned sessions,
  reporting currency variance, column collision defence, CRM field mapping,
  error branches, and edge cases.

Test style mirrors tests/test_data.py: function-level pytest, no class wrappers.
"""

import pytest
import pandas as pd

from ingest import (
    SUPPORTED_CURRENCIES,
    FX_RATES,
    REQUIRED_CRM_FIELDS,
    convert_cost,
    auto_suggest_crm_columns,
    ingest,
)


# ---------------------------------------------------------------------------
# Module-level helper (NOT a pytest fixture — plain function used by tests)
# ---------------------------------------------------------------------------

def _csv_bytes(rows: list[dict]) -> bytes:
    """Build a CSV byte string from a list of dicts via pandas."""
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


# ---------------------------------------------------------------------------
# Module-level constants for reuse across integration and error-branch tests
# ---------------------------------------------------------------------------

_GOOGLE_ROWS = [
    {
        "session_id": "sess_1",
        "campaign_id": "cmp_a",
        "clicks": 10,
        "impressions": 100,
        "cost_local": 5.0,
        "conversion_rate": 0.01,
    },
    {
        "session_id": "sess_2",
        "campaign_id": "cmp_a",
        "clicks": 20,
        "impressions": 200,
        "cost_local": 7.5,
        "conversion_rate": 0.02,
    },
    {
        "session_id": "sess_3",
        "campaign_id": "cmp_b",
        "clicks": 15,
        "impressions": 150,
        "cost_local": 6.0,
        "conversion_rate": 0.03,
    },
]

_META_ROWS = [
    {
        "session_id": "sess_1",
        "campaign_id": "cmp_a",
        "clicks": 3,
        "impressions": 40,
        "cost_local": 2.0,
        "conversion_rate": 0.05,
    },
    {
        "session_id": "sess_4",
        "campaign_id": "cmp_c",
        "clicks": 8,
        "impressions": 90,
        "cost_local": 4.0,
        "conversion_rate": 0.04,
    },
]

_CRM_STANDARD_ROWS = [
    {
        "session_id": "sess_1",
        "lead_status": "Qualified",
        "projected_value": 1000.0,
        "sales_notes": "Good lead",
    },
    {
        "session_id": "sess_2",
        "lead_status": "Disqualified",
        "projected_value": 0.0,
        "sales_notes": "Bad fit",
    },
    {
        "session_id": "sess_3",
        "lead_status": "Nurture",
        "projected_value": 500.0,
        "sales_notes": "Warm",
    },
    {
        "session_id": "sess_4",
        "lead_status": "Qualified",
        "projected_value": 2000.0,
        "sales_notes": "Hot",
    },
]

# Identity mapping: each required field maps to itself (standard CRM columns)
_IDENTITY_FIELD_MAP = {f: f for f in REQUIRED_CRM_FIELDS}


# ===========================================================================
# Task 1: Constant and helper tests (9 tests)
# ===========================================================================


def test_supported_currencies_exact_list():
    """SUPPORTED_CURRENCIES must be exactly the 8 ISO codes in canonical order (D-10)."""
    assert SUPPORTED_CURRENCIES == ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR", "SGD"]


def test_fx_rates_usd_anchor():
    """FX_RATES["USD"] == 1.0; all 8 currencies present; all rates positive (D-10)."""
    assert FX_RATES["USD"] == 1.0
    assert set(FX_RATES.keys()) == set(SUPPORTED_CURRENCIES)
    assert all(v > 0 for v in FX_RATES.values())


def test_required_crm_fields_exact():
    """REQUIRED_CRM_FIELDS must be exactly the 4-element canonical list (D-06)."""
    assert REQUIRED_CRM_FIELDS == [
        "session_id",
        "lead_status",
        "projected_value",
        "sales_notes",
    ]


def test_convert_cost_usd_identity():
    """convert_cost(100.0, 'USD', 'USD') must return 100.0 exactly."""
    assert convert_cost(100.0, "USD", "USD") == 100.0


def test_convert_cost_round_trip():
    """USD → EUR → USD must recover the original value within floating-point tolerance."""
    converted = convert_cost(100.0, "USD", "EUR")
    recovered = convert_cost(converted, "EUR", "USD")
    assert abs(recovered - 100.0) < 1e-9


def test_convert_cost_unknown_currency_raises():
    """convert_cost with an unsupported code must raise ValueError naming the code and 'Supported'."""
    with pytest.raises(ValueError) as exc_info:
        convert_cost(100.0, "USD", "XYZ")
    assert "XYZ" in str(exc_info.value)
    assert "Supported" in str(exc_info.value)


def test_auto_suggest_exact_match():
    """Exact column names in the CRM CSV must map to themselves."""
    cols = ["session_id", "lead_status", "projected_value", "sales_notes", "extra"]
    result = auto_suggest_crm_columns(cols)
    for field in REQUIRED_CRM_FIELDS:
        assert result[field] == field, (
            f"Expected '{field}' to map to itself, got {result[field]!r}"
        )


def test_auto_suggest_close_match():
    """Columns with close (but not exact) names should produce at least one non-None suggestion."""
    cols = ["sessionid", "lead_state", "value", "notes_text"]
    result = auto_suggest_crm_columns(cols)
    assert any(v is not None for v in result.values()), (
        "Expected difflib to suggest at least one close match but all were None"
    )


def test_auto_suggest_no_match():
    """Completely unrelated columns must all return None — no aggressive garbage matches."""
    cols = ["x", "y", "z"]
    result = auto_suggest_crm_columns(cols)
    assert all(v is None for v in result.values()), (
        f"Expected all None but got: {result}"
    )


# ===========================================================================
# Task 2: ingest() integration tests (8 tests)
# ===========================================================================


def test_ingest_happy_path_two_platforms():
    """Two platforms (Google USD + Meta EUR) + full CRM, reporting USD → 5 rows total."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
        ("Meta Ads", _csv_bytes(_META_ROWS), "EUR", "meta_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")

    # All 3 Google rows have CRM matches + all 2 Meta rows have CRM matches = 5 total
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"

    # Source-prefixed numeric columns must be present; plain 'clicks' must be absent
    assert "google_ads_clicks" in df.columns
    assert "meta_ads_clicks" in df.columns
    assert "clicks" not in df.columns

    # Both platform labels must appear
    assert set(df["platform"].unique()) == {"Google Ads", "Meta Ads"}

    # Meta cost_usd must be FX-converted from EUR to USD
    meta_row = df[df["platform"] == "Meta Ads"].iloc[0]
    # The first Meta row has cost_local=2.0 EUR; after conversion: 2.0 * FX_RATES["EUR"] / FX_RATES["USD"]
    expected_meta_cost = 2.0 * FX_RATES["EUR"] / FX_RATES["USD"]
    assert abs(meta_row["cost_usd"] - expected_meta_cost) < 1e-6, (
        f"Meta cost_usd expected ~{expected_meta_cost:.6f}, got {meta_row['cost_usd']:.6f}"
    )


def test_ingest_platform_and_currency_columns_present():
    """Every output row must have non-null 'platform' and 'currency_code'; both currencies present."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
        ("Meta Ads", _csv_bytes(_META_ROWS), "EUR", "meta_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")

    assert df["platform"].notna().all(), "Found null values in 'platform' column"
    assert df["currency_code"].notna().all(), "Found null values in 'currency_code' column"
    assert set(df["currency_code"].unique()) == {"USD", "EUR"}, (
        f"Expected {{'USD', 'EUR'}} but got {set(df['currency_code'].unique())}"
    )


def test_ingest_no_xy_suffixes_after_merge():
    """No column in the output should end with '_x' or '_y' (source-prefix collision guard)."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
        ("Meta Ads", _csv_bytes(_META_ROWS), "EUR", "meta_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")

    bad_cols = [c for c in df.columns if c.endswith("_x") or c.endswith("_y")]
    assert not bad_cols, f"Columns with _x/_y suffix found: {bad_cols}"


def test_ingest_orphaned_sessions_dropped():
    """Sessions in ad platforms but not in CRM are dropped by the inner merge."""
    # CRM has only sess_1 and sess_2 (sess_3 and sess_4 are absent)
    crm_partial = [
        {"session_id": "sess_1", "lead_status": "Qualified", "projected_value": 1000.0, "sales_notes": "Good"},
        {"session_id": "sess_2", "lead_status": "Disqualified", "projected_value": 0.0, "sales_notes": "Bad"},
    ]
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
        ("Meta Ads", _csv_bytes(_META_ROWS), "EUR", "meta_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(crm_partial), _IDENTITY_FIELD_MAP, "USD")

    # Google sess_3 (no CRM) and Meta sess_4 (no CRM) are dropped.
    # Survivors: Google sess_1, Google sess_2, Meta sess_1 = 3 rows
    assert len(df) == 3, f"Expected 3 rows after dropping orphans, got {len(df)}"
    assert set(df["session_id"].unique()) == {"sess_1", "sess_2"}, (
        f"Expected only sess_1 and sess_2 in output, got {set(df['session_id'].unique())}"
    )


def test_ingest_reporting_currency_changes_cost_usd():
    """Same inputs with different reporting_currency produce proportionally different cost_usd."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    crm_bytes = _csv_bytes(_CRM_STANDARD_ROWS)

    df_usd = ingest(platform_csvs, crm_bytes, _IDENTITY_FIELD_MAP, "USD")
    df_eur = ingest(platform_csvs, crm_bytes, _IDENTITY_FIELD_MAP, "EUR")

    # Google sess_1 has cost_local=5.0 USD
    # With reporting="USD": cost_usd = 5.0 * FX_RATES["USD"] / FX_RATES["USD"] = 5.0
    # With reporting="EUR": cost_usd = 5.0 * FX_RATES["USD"] / FX_RATES["EUR"]
    row_usd = df_usd[df_usd["session_id"] == "sess_1"].iloc[0]
    row_eur = df_eur[df_eur["session_id"] == "sess_1"].iloc[0]

    expected_usd_cost = 5.0 * FX_RATES["USD"] / FX_RATES["USD"]  # = 5.0
    expected_eur_cost = 5.0 * FX_RATES["USD"] / FX_RATES["EUR"]

    assert abs(row_usd["cost_usd"] - expected_usd_cost) < 1e-6, (
        f"USD reporting: expected ~{expected_usd_cost:.6f}, got {row_usd['cost_usd']:.6f}"
    )
    assert abs(row_eur["cost_usd"] - expected_eur_cost) < 1e-6, (
        f"EUR reporting: expected ~{expected_eur_cost:.6f}, got {row_eur['cost_usd']:.6f}"
    )


def test_ingest_empty_platforms_list_raises():
    """ingest() with an empty platform list must raise ValueError."""
    with pytest.raises(ValueError):
        ingest([], _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")


def test_ingest_all_none_bytes_raises():
    """ingest() where all platform csv_bytes are None must raise ValueError."""
    platform_csvs = [
        ("Google Ads", None, "USD", "google_ads"),
        ("Meta Ads", None, "EUR", "meta_ads"),
    ]
    with pytest.raises(ValueError):
        ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")


def test_ingest_skips_none_bytes_platform():
    """A platform with None bytes is silently skipped; the other platform's rows are returned."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
        ("Meta Ads", None, "EUR", "meta_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")

    # Only Google Ads data should appear (3 rows, all with CRM matches)
    assert set(df["platform"].unique()) == {"Google Ads"}, (
        f"Expected only 'Google Ads' but got {set(df['platform'].unique())}"
    )
    assert len(df) == 3, f"Expected 3 rows from Google Ads only, got {len(df)}"


# ===========================================================================
# Task 3: Error-branch tests (7 tests)
# ===========================================================================


def test_ingest_unsupported_platform_currency_raises():
    """Platform with unsupported currency code must raise ValueError naming the code and 'Supported'."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "XYZ", "google_ads"),
    ]
    with pytest.raises(ValueError) as exc_info:
        ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")
    assert "XYZ" in str(exc_info.value)
    assert "Supported" in str(exc_info.value)


def test_ingest_unsupported_reporting_currency_raises():
    """Unsupported reporting_currency must raise ValueError naming the code."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    with pytest.raises(ValueError) as exc_info:
        ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "XYZ")
    assert "XYZ" in str(exc_info.value)


def test_ingest_duplicate_crm_session_id_raises_merge_error():
    """Duplicate session_id in the CRM CSV must raise pd.errors.MergeError (validate='m:1')."""
    crm_dup_rows = [
        {"session_id": "sess_1", "lead_status": "Qualified", "projected_value": 1000.0, "sales_notes": "A"},
        {"session_id": "sess_1", "lead_status": "Qualified", "projected_value": 1000.0, "sales_notes": "B"},
    ]
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    with pytest.raises(pd.errors.MergeError):
        ingest(platform_csvs, _csv_bytes(crm_dup_rows), _IDENTITY_FIELD_MAP, "USD")


def test_ingest_crm_field_mapping_non_standard_names():
    """CRM with non-standard column names must be correctly mapped to canonical field names."""
    crm_nonstandard = [
        {"sid": "sess_1", "status": "Qualified", "value": 1000.0, "notes": "Good"},
        {"sid": "sess_2", "status": "Disqualified", "value": 0.0, "notes": "Bad"},
        {"sid": "sess_3", "status": "Nurture", "value": 500.0, "notes": "Warm"},
    ]
    field_map = {
        "session_id": "sid",
        "lead_status": "status",
        "projected_value": "value",
        "sales_notes": "notes",
    }
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(crm_nonstandard), field_map, "USD")

    # Canonical names must appear in output; non-standard names must not
    assert "session_id" in df.columns
    assert "lead_status" in df.columns
    assert "projected_value" in df.columns
    assert "sales_notes" in df.columns
    assert "sid" not in df.columns
    assert "status" not in df.columns
    assert "value" not in df.columns
    assert "notes" not in df.columns

    # Verify values are correctly mapped
    assert set(df["lead_status"].unique()).issubset({"Qualified", "Disqualified", "Nurture"})


def test_ingest_incomplete_crm_field_mapping_raises():
    """CRM field_map missing a required field must raise ValueError mentioning the missing field."""
    # Only 3 of 4 required fields mapped — 'sales_notes' is absent
    incomplete_field_map = {
        "session_id": "session_id",
        "lead_status": "lead_status",
        "projected_value": "projected_value",
        # "sales_notes" is deliberately missing
    }
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    with pytest.raises(ValueError) as exc_info:
        ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), incomplete_field_map, "USD")
    # ingest.py raises: "CRM field mapping incomplete or refers to missing column: sales_notes → None"
    assert "sales_notes" in str(exc_info.value)


def test_ingest_field_mapping_to_missing_column_raises():
    """CRM field_map referencing a non-existent column must raise ValueError."""
    # sales_notes maps to a column that doesn't exist in the CRM CSV
    bad_field_map = {
        "session_id": "session_id",
        "lead_status": "lead_status",
        "projected_value": "projected_value",
        "sales_notes": "nonexistent_column",
    }
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    with pytest.raises(ValueError) as exc_info:
        ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), bad_field_map, "USD")
    # ingest.py raises: "CRM field mapping incomplete or refers to missing column: sales_notes → 'nonexistent_column'"
    assert "nonexistent_column" in str(exc_info.value)


def test_ingest_column_collision_source_prefix_renames():
    """A non-key column with the same name in two platforms must be source-prefixed in output."""
    # Both platform CSVs contain an 'extra_col' column — same name, different platforms
    plat_a_rows = [
        {
            "session_id": "sess_1",
            "campaign_id": "cmp_a",
            "clicks": 10,
            "impressions": 100,
            "cost_local": 5.0,
            "conversion_rate": 0.01,
            "extra_col": "a_val",
        }
    ]
    plat_b_rows = [
        {
            "session_id": "sess_1",
            "campaign_id": "cmp_a",
            "clicks": 3,
            "impressions": 40,
            "cost_local": 2.0,
            "conversion_rate": 0.05,
            "extra_col": "b_val",
        }
    ]
    # CRM with just sess_1 so merge succeeds
    crm_rows = [
        {"session_id": "sess_1", "lead_status": "Qualified", "projected_value": 1000.0, "sales_notes": "Good"},
    ]
    platform_csvs = [
        ("Google Ads", _csv_bytes(plat_a_rows), "USD", "google_ads"),
        ("Meta Ads", _csv_bytes(plat_b_rows), "USD", "meta_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(crm_rows), _IDENTITY_FIELD_MAP, "USD")

    # Both source-prefixed variants must be present
    assert "google_ads_extra_col" in df.columns, (
        f"Expected 'google_ads_extra_col' in columns: {list(df.columns)}"
    )
    assert "meta_ads_extra_col" in df.columns, (
        f"Expected 'meta_ads_extra_col' in columns: {list(df.columns)}"
    )

    # Plain name and _x/_y variants must NOT be present
    assert "extra_col" not in df.columns, "Plain 'extra_col' should have been source-prefixed"
    assert "extra_col_x" not in df.columns, "Found _x suffix — source-prefix rename failed"
    assert "extra_col_y" not in df.columns, "Found _y suffix — source-prefix rename failed"

    # Merge must have produced rows
    assert len(df) > 0, "Expected at least one merged row"


# ===========================================================================
# Task 4: CRM extra column pass-through tests (Phase 10 D-06) — 2 tests
# ===========================================================================


def test_ingest_extra_crm_columns_preserved_with_prefix():
    """CRM CSV with 5 columns (4 required + 1 extra 'deal_stage') → merged_df contains 'crm_deal_stage'."""
    crm_with_extra = [
        {"session_id": "sess_1", "lead_status": "Qualified", "projected_value": 1000.0,
         "sales_notes": "Good lead", "deal_stage": "Proposal"},
        {"session_id": "sess_2", "lead_status": "Disqualified", "projected_value": 0.0,
         "sales_notes": "Bad fit", "deal_stage": "Lost"},
        {"session_id": "sess_3", "lead_status": "Nurture", "projected_value": 500.0,
         "sales_notes": "Warm", "deal_stage": "Prospecting"},
    ]
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(crm_with_extra), _IDENTITY_FIELD_MAP, "USD")

    # Extra column must be present with crm_ prefix
    assert "crm_deal_stage" in df.columns, (
        f"Expected 'crm_deal_stage' in columns: {list(df.columns)}"
    )
    # Values must be preserved
    assert "Proposal" in df["crm_deal_stage"].values, "Expected 'Proposal' in crm_deal_stage"
    # Original name must not be present
    assert "deal_stage" not in df.columns, "Plain 'deal_stage' should have been renamed to 'crm_deal_stage'"


def test_ingest_no_extra_crm_columns_produces_no_crm_prefix_cols():
    """CRM CSV with exactly 4 required columns → merged_df does NOT contain any 'crm_' columns."""
    platform_csvs = [
        ("Google Ads", _csv_bytes(_GOOGLE_ROWS), "USD", "google_ads"),
    ]
    df = ingest(platform_csvs, _csv_bytes(_CRM_STANDARD_ROWS), _IDENTITY_FIELD_MAP, "USD")

    crm_extra_cols = [c for c in df.columns if c.startswith("crm_")]
    assert crm_extra_cols == [], (
        f"Expected no crm_-prefixed columns but found: {crm_extra_cols}"
    )
