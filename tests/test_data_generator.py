"""
Phase 9 — multi-source-ingestion: Nyquist gap-fill tests for data_generator.py.

Gaps covered (09-02-PLAN.md):
  G1 — PLATFORM_CURRENCIES exact mapping
  G2 — Per-platform generator schema and minimum row count
  G3 — Multi-platform session_id overlap (fan-out coverage)
  G4 — Fixture CSVs exist on disk with correct schema and row count
  G5 — write_csvs() idempotency (same content on second run)
  G6 — All 4 fixture CSVs flow through ingest.ingest() end-to-end

Test style: module-level functions, no class wrappers, mirrors test_ingest.py conventions.
"""

import pathlib
import tempfile
from collections import Counter

import pandas as pd
import pytest

import data_generator
from ingest import REQUIRED_CRM_FIELDS, ingest

# Stable path to the data/ directory relative to this file's parent
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"

# Canonical 6-column schema every ad-platform CSV must expose
_PLATFORM_COLUMNS = [
    "session_id",
    "campaign_id",
    "clicks",
    "impressions",
    "cost_local",
    "conversion_rate",
]

# Slug map used for G6 end-to-end test — mirrors the mapping in the inline smoke-test comment
_SLUG_MAP = {
    "Google Ads": "google_ads",
    "Meta Ads": "meta_ads",
    "LinkedIn Ads": "linkedin_ads",
    "Custom": "custom_ads",
}

# Generator functions paired with their display names (for G2 / G3 loops)
_GENERATORS = [
    ("Google Ads", data_generator.generate_google_ads),
    ("Meta Ads", data_generator.generate_meta_ads),
    ("LinkedIn Ads", data_generator.generate_linkedin_ads),
    ("Custom", data_generator.generate_custom_ads),
]


# ---------------------------------------------------------------------------
# G1 — PLATFORM_CURRENCIES exact mapping (INGEST-01 / 09-02-01)
# ---------------------------------------------------------------------------

def test_platform_currencies_dict():
    """PLATFORM_CURRENCIES must map exactly the 4 expected platform → currency pairs."""
    expected = {
        "Google Ads": "USD",
        "Meta Ads": "EUR",
        "LinkedIn Ads": "GBP",
        "Custom": "USD",
    }
    assert data_generator.PLATFORM_CURRENCIES == expected, (
        f"PLATFORM_CURRENCIES mismatch.\n"
        f"Expected: {expected}\n"
        f"Actual:   {data_generator.PLATFORM_CURRENCIES}"
    )


# ---------------------------------------------------------------------------
# G2 — Per-platform generator schema and row count (INGEST-01 / 09-02-01)
# ---------------------------------------------------------------------------

def test_generator_schemas_correct():
    """Each generator must return a DataFrame with exactly the 6 canonical columns and >= 3 rows."""
    for display_name, generator_fn in _GENERATORS:
        df = generator_fn()
        assert list(df.columns) == _PLATFORM_COLUMNS, (
            f"{display_name}: expected columns {_PLATFORM_COLUMNS}, got {list(df.columns)}"
        )
        assert len(df) >= 3, (
            f"{display_name}: expected >= 3 rows, got {len(df)}"
        )


# ---------------------------------------------------------------------------
# G3 — Multi-platform session_id overlap (INGEST-01 / 09-02-01)
# ---------------------------------------------------------------------------

def test_multi_platform_session_overlap():
    """At least 2 session_id values must appear in 2 or more of the 4 platform DataFrames."""
    all_sessions: list[str] = []
    for _display_name, generator_fn in _GENERATORS:
        all_sessions.extend(generator_fn()["session_id"].tolist())

    counts = Counter(all_sessions)
    multi_platform_sessions = [sid for sid, count in counts.items() if count >= 2]

    assert len(multi_platform_sessions) >= 2, (
        f"Expected >= 2 session_ids appearing in 2+ platforms for fan-out coverage, "
        f"got {len(multi_platform_sessions)}: {multi_platform_sessions}"
    )


# ---------------------------------------------------------------------------
# G4 — Fixture CSVs exist on disk with correct schema and row count (INGEST-01 / 09-02-02)
# ---------------------------------------------------------------------------

def test_fixture_csvs_exist_on_disk():
    """All 4 ad-platform fixture CSVs must exist with the canonical 6-column schema and >= 3 rows."""
    fixture_files = [
        "google_ads.csv",
        "meta_ads.csv",
        "linkedin_ads.csv",
        "custom_ads.csv",
    ]
    for filename in fixture_files:
        path = _DATA_DIR / filename
        assert path.exists(), f"Fixture CSV not found on disk: {path}"
        df = pd.read_csv(path)
        assert list(df.columns) == _PLATFORM_COLUMNS, (
            f"{filename}: expected columns {_PLATFORM_COLUMNS}, got {list(df.columns)}"
        )
        assert len(df) >= 3, (
            f"{filename}: expected >= 3 rows, got {len(df)}"
        )


# ---------------------------------------------------------------------------
# G5 — write_csvs() idempotency (INGEST-01 / 09-02-02)
# ---------------------------------------------------------------------------

def test_write_csvs_idempotent():
    """Running write_csvs() twice in a tmp_path must produce byte-identical file contents."""
    platform_files = [
        "google_ads.csv",
        "meta_ads.csv",
        "linkedin_ads.csv",
        "custom_ads.csv",
    ]

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_path = pathlib.Path(tmp_str)

        # First write
        data_generator.write_csvs(tmp_path)
        first_dfs: dict[str, pd.DataFrame] = {
            name: pd.read_csv(tmp_path / name) for name in platform_files
        }

        # Second write — must overwrite without error and produce the same content
        data_generator.write_csvs(tmp_path)
        second_dfs: dict[str, pd.DataFrame] = {
            name: pd.read_csv(tmp_path / name) for name in platform_files
        }

        for name in platform_files:
            pd.testing.assert_frame_equal(
                first_dfs[name],
                second_dfs[name],
                check_exact=False,
                rtol=1e-9,
                obj=f"{name} idempotency",
            )


# ---------------------------------------------------------------------------
# G6 — All 4 fixture CSVs end-to-end through ingest() (INGEST-01 + INGEST-03 / 09-02-03)
# ---------------------------------------------------------------------------

def test_all_fixtures_through_ingest():
    """All 4 demo fixture CSVs must flow through ingest.ingest() and produce a valid merged DataFrame.

    Asserts:
    - Non-empty merged result
    - All 4 platform labels present
    - All 3 currency codes present (USD from Google/Custom, EUR from Meta, GBP from LinkedIn)
    - Source-prefixed numeric columns present for each platform
    """
    platform_csvs = []
    for display_name, currency in data_generator.PLATFORM_CURRENCIES.items():
        slug = _SLUG_MAP[display_name]
        csv_path = _DATA_DIR / f"{slug}.csv"
        assert csv_path.exists(), (
            f"Fixture file missing: {csv_path} — run `python data_generator.py` first"
        )
        csv_bytes = csv_path.read_bytes()
        platform_csvs.append((display_name, csv_bytes, currency, slug))

    crm_bytes = (_DATA_DIR / "crm_data.csv").read_bytes()
    # Identity field map: crm_data.csv already uses the canonical REQUIRED_CRM_FIELDS column names
    field_map = {f: f for f in REQUIRED_CRM_FIELDS}

    merged = ingest(platform_csvs, crm_bytes, field_map, "USD")

    # Must have at least one merged row
    assert len(merged) > 0, (
        "ingest() produced zero rows — session_id overlap between fixture CSVs and CRM broken"
    )

    # All 4 platform labels must appear
    expected_platforms = {"Google Ads", "Meta Ads", "LinkedIn Ads", "Custom"}
    actual_platforms = set(merged["platform"].unique())
    assert actual_platforms == expected_platforms, (
        f"Platform set mismatch.\nExpected: {expected_platforms}\nActual: {actual_platforms}"
    )

    # All 3 source currency codes must appear (USD + EUR + GBP)
    expected_currencies = {"USD", "EUR", "GBP"}
    actual_currencies = set(merged["currency_code"].unique())
    assert actual_currencies == expected_currencies, (
        f"Currency code set mismatch.\nExpected: {expected_currencies}\nActual: {actual_currencies}"
    )

    # Source-prefixed numeric columns must exist for each platform slug
    for slug in _SLUG_MAP.values():
        col = f"{slug}_clicks"
        assert col in merged.columns, (
            f"Expected source-prefixed column '{col}' in merged DataFrame. "
            f"Columns present: {sorted(merged.columns.tolist())}"
        )
