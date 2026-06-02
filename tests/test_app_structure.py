"""
Phase 9 — multi-source-ingestion: Nyquist gap-fill tests for app.py structure.

Gaps covered (09-03-PLAN.md):
  G7 — app.py imports SUPPORTED_CURRENCIES, REQUIRED_CRM_FIELDS from ingest,
       and references auto_suggest_crm_columns (INGEST-01, INGEST-02 / 09-03-01)
  G8 — app.py calls ingest(), references crm_field_map session state key,
       and references reporting_currency (INGEST-01, INGEST-02 / 09-03-03)

Test style: read app.py as text and assert required strings are present,
mirroring the pattern from tests/test_phase7_landing.py.
"""

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
APP_PY = PROJECT_ROOT / "app.py"


# ---------------------------------------------------------------------------
# G7 — app.py imports SUPPORTED_CURRENCIES, REQUIRED_CRM_FIELDS, and
#       auto_suggest_crm_columns from ingest (INGEST-01, INGEST-02 / 09-03-01)
# ---------------------------------------------------------------------------

def test_app_imports_ingest_constants():
    """app.py must import SUPPORTED_CURRENCIES and REQUIRED_CRM_FIELDS from ingest
    (not hardcoded) and must reference ingest.auto_suggest_crm_columns."""
    source = APP_PY.read_text()

    # Must import from ingest — not use inline string lists
    assert "from ingest import" in source, (
        "app.py does not contain 'from ingest import' — constants may be hardcoded"
    )

    # SUPPORTED_CURRENCIES must be imported (drives selectbox options, never hardcoded)
    assert "SUPPORTED_CURRENCIES" in source, (
        "app.py does not reference SUPPORTED_CURRENCIES — currency list may be hardcoded"
    )

    # REQUIRED_CRM_FIELDS must be imported (drives the CRM mapping UI loop)
    assert "REQUIRED_CRM_FIELDS" in source, (
        "app.py does not reference REQUIRED_CRM_FIELDS — field list may be hardcoded"
    )

    # auto_suggest_crm_columns must be referenced (powers the CRM field auto-suggest UI)
    assert "auto_suggest_crm_columns" in source, (
        "app.py does not reference auto_suggest_crm_columns — CRM auto-suggest UI is absent"
    )


# ---------------------------------------------------------------------------
# G8 — app.py calls ingest() and references crm_field_map and reporting_currency
#       (INGEST-01, INGEST-02 / 09-03-03)
# ---------------------------------------------------------------------------

def test_app_calls_ingest():
    """app.py must call ingest() to wire the upload pipeline, reference the
    crm_field_map session state key, and reference reporting_currency."""
    source = APP_PY.read_text()

    # ingest( must appear as a function call (not just an import)
    assert "ingest(" in source, (
        "app.py does not call ingest() — the upload pipeline is not wired to the ingest module"
    )

    # crm_field_map must appear as a session state key
    assert "crm_field_map" in source, (
        "app.py does not reference 'crm_field_map' — the CRM field mapping session state key is absent"
    )

    # reporting_currency must appear (sidebar selectbox key or ingest() argument)
    assert "reporting_currency" in source, (
        "app.py does not reference 'reporting_currency' — the sidebar currency selectbox is absent"
    )
