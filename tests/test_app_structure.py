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


# ---------------------------------------------------------------------------
# Gap 2 — INGEST-01/02: "Load Demo Data" handler sets crm_field_map to the
#          identity mapping {f: f for f in REQUIRED_CRM_FIELDS}
# ---------------------------------------------------------------------------

def test_app_load_demo_sets_crm_field_map():
    """When the Load Demo Data button fires, app.py must set crm_field_map to
    the identity mapping built from REQUIRED_CRM_FIELDS.  This is verified
    structurally: all four load-bearing strings must appear in the source."""
    source = APP_PY.read_text()

    # The sidebar button key used as the click target
    assert "load_demo_sidebar" in source, (
        "app.py does not contain 'load_demo_sidebar' — the Load Demo Data button key is absent"
    )

    # crm_field_map must be set inside the handler
    assert "crm_field_map" in source, (
        "app.py does not reference 'crm_field_map' — the session-state key is absent"
    )

    # REQUIRED_CRM_FIELDS must be referenced (identity mapping iterates over it)
    assert "REQUIRED_CRM_FIELDS" in source, (
        "app.py does not reference REQUIRED_CRM_FIELDS — identity mapping is not built from it"
    )

    # The identity mapping pattern {f: f for f in ...} must appear verbatim
    assert "{f: f for f in REQUIRED_CRM_FIELDS}" in source, (
        "app.py does not contain '{f: f for f in REQUIRED_CRM_FIELDS}' — "
        "crm_field_map is not set to the identity mapping on Load Demo Data"
    )


# ---------------------------------------------------------------------------
# Gap 3 — AGENT-02 app-layer: source_platforms is rendered inside the results
#          expander via st.caption
# ---------------------------------------------------------------------------

def test_app_renders_source_platforms_in_expander():
    """The results expander block must reference source_platforms and render it
    via st.caption — ensuring platform attribution appears in the per-campaign
    detail view."""
    source = APP_PY.read_text()

    # source_platforms must be referenced (conditional render guard + join)
    assert "source_platforms" in source, (
        "app.py does not reference 'source_platforms' — platform attribution is absent from results"
    )

    # st.caption must appear in the same file as the expander (rendering vehicle)
    assert "st.caption" in source, (
        "app.py does not call st.caption — source_platforms rendering path is absent"
    )

    # st.expander must exist (the results block context manager)
    assert "st.expander" in source, (
        "app.py does not use st.expander — the per-campaign results block is absent"
    )

    # The actual caption line combining source_platforms must be present
    assert "', '.join(c.source_platforms)" in source, (
        "app.py does not contain \"', '.join(c.source_platforms)\" — "
        "source_platforms values are not joined and rendered inside the expander"
    )


# ---------------------------------------------------------------------------
# Gap 4 — AGENT-03 app-layer: token gate is fully wired in app.py
# ---------------------------------------------------------------------------

def test_app_token_gate_wired():
    """The Phase 10 token gate must be fully wired: threshold constant, warning
    button label, session-state confirmation key, and the token-counting helper
    must all be present in app.py."""
    source = APP_PY.read_text()

    # 60_000 threshold constant (with underscores as written in source)
    assert "60_000" in source, (
        "app.py does not contain '60_000' — the token-gate threshold is absent"
    )

    # The bypass button label shown to the user
    assert "Continue anyway" in source, (
        "app.py does not contain 'Continue anyway' — the token-gate bypass button is absent"
    )

    # Session-state key that records the user's bypass confirmation
    assert "token_warning_confirmed" in source, (
        "app.py does not contain 'token_warning_confirmed' — "
        "the token-gate confirmation state key is absent"
    )

    # The helper function that counts tokens before calling the LLM
    assert "count_prompt_tokens" in source, (
        "app.py does not reference 'count_prompt_tokens' — "
        "the token-counting call is absent from the token gate"
    )
