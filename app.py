import os
import pathlib

import streamlit as st
import pandas as pd
from openai import OpenAI
from data import compute_campaign_agg
from dotenv import load_dotenv
import llm
from llm import run_analysis, count_prompt_tokens
from ui_helpers import _badge_html, _pct_html, build_exec_summary_html
from ingest import SUPPORTED_CURRENCIES, REQUIRED_CRM_FIELDS, auto_suggest_crm_columns, ingest

load_dotenv()

BRANDED_HEADER_HTML = """
<div style="
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 16px 0;
  border-bottom: 1px solid #e6e9ef;
  margin-bottom: 20px;
  font-family: 'IBM Plex Sans', sans-serif;
">
  <div>
    <span style="font-size: 22px; font-weight: 600; color: #262730;">⚡ Performance Plus</span>
    <span style="
      display: block;
      font-size: 14px;
      font-weight: 400;
      color: #808495;
      margin-top: 2px;
    ">AI-powered budget decisions from your CRM notes</span>
  </div>
  <a href="/" target="_self" style="
    font-size: 13px;
    font-weight: 400;
    color: #808495;
    text-decoration: none;
  ">← Back to site</a>
</div>
"""

# per D-04, D-05: module-level flag; DEMO_MODE=1 activates offline fixture path
DEMO_MODE = os.environ.get("DEMO_MODE") == "1"

st.set_page_config(
    page_title="Performance Plus",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("OpenAI API Key")
    # per D-04: in DEMO_MODE with no live key, show green badge instead of key input
    if DEMO_MODE and llm.client is None:
        st.success("✅ Demo Mode — running with cached results")
    else:
        api_key_input = st.text_input(
            "Paste your key",
            type="password",
            placeholder="sk-...",
            help="Used only for this session — never stored.",
            label_visibility="collapsed",
        )
        if api_key_input:
            llm.client = OpenAI(api_key=api_key_input)
        elif not llm.client:
            llm.client = None

        if llm.client is not None:
            st.success("Key set — ready to analyse.")
        else:
            st.warning("Enter your OpenAI API key to enable Run Analysis.")
            st.markdown(
                "Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)",
                unsafe_allow_html=False,
            )

    # per D-12 / UI-SPEC section 4.5: Reporting Currency selectbox after API key block
    st.subheader("Reporting Currency")
    st.selectbox(
        label="Output currency",
        options=SUPPORTED_CURRENCIES,
        index=SUPPORTED_CURRENCIES.index("INR"),
        key="reporting_currency",
        help="All platform costs are converted to this currency before aggregation.",
        label_visibility="collapsed",
    )

    # per D-16 / UI-SPEC section 4.6: Demo Data section replaces main-area button
    st.subheader("Demo Data")
    if st.button("Load Demo Data", type="primary", key="load_demo_sidebar"):
        try:
            data_dir = pathlib.Path(__file__).parent / "data"
            st.session_state["google_ads_bytes"] = (data_dir / "google_ads.csv").read_bytes()
            st.session_state["meta_ads_bytes"] = (data_dir / "meta_ads.csv").read_bytes()
            st.session_state["linkedin_ads_bytes"] = (data_dir / "linkedin_ads.csv").read_bytes()
            st.session_state["custom_ads_bytes"] = (data_dir / "custom_ads.csv").read_bytes()
            st.session_state["crm_bytes"] = (data_dir / "crm_data.csv").read_bytes()
            st.session_state["demo_mode_active"] = True
        except FileNotFoundError:
            st.error("Demo data files not found. Run: python data_generator.py")
            st.stop()

    if st.session_state.get("demo_mode_active"):
        st.caption("Demo data loaded — 4 platforms + CRM.")

# per D-05: info banner renders in main column above title when DEMO_MODE=1
if DEMO_MODE:
    st.info("ℹ️ Running in demo mode — cached results, no live API call")

st.markdown(BRANDED_HEADER_HTML, unsafe_allow_html=True)

# per UI-SPEC section 4.8: 11-key session_state initialization block
_state_defaults = {
    "merged_df": None,
    "campaign_agg": None,
    "analysis_result": None,
    # Phase 9 additions:
    "google_ads_bytes": None,
    "meta_ads_bytes": None,
    "linkedin_ads_bytes": None,
    "custom_ads_bytes": None,
    "crm_bytes": None,
    "crm_field_map": None,
    "reporting_currency": "INR",
    "demo_mode_active": False,
    # Phase 10 addition:
    "token_warning_confirmed": False,
}
for k, v in _state_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# per UI-SPEC section 4.9: updated CSV schema reference for multi-platform format
st.markdown("**EXPECTED CSV SCHEMAS (FOR REFERENCE)**")
st.code("Ad platform CSVs: session_id, campaign_id, clicks, impressions, cost_local, conversion_rate", language=None)
st.code("CRM CSV: any column names — you'll map them to standard fields below", language=None)

# ---------------------------------------------------------------------------
# Phase 9 D-17: Platform upload slot configuration — DRY constant consumed by
# _render_platform_slot() and the gate logic below.
# Tuple: (display_name, slug, bytes_key, uploader_key, currency_key, default_currency)
# Default currencies match data_generator.PLATFORM_CURRENCIES (D-17) — kept inline
# so the UI default works without importing data_generator at runtime.
# ---------------------------------------------------------------------------
_PLATFORMS = [
    ("Google Ads",    "google_ads",    "google_ads_bytes",    "google_ads_uploader",    "google_ads_currency",    "USD"),
    ("Meta Ads",      "meta_ads",      "meta_ads_bytes",      "meta_ads_uploader",      "meta_ads_currency",      "EUR"),
    ("LinkedIn Ads",  "linkedin_ads",  "linkedin_ads_bytes",  "linkedin_ads_uploader",  "linkedin_ads_currency",  "GBP"),
    ("Custom",        "custom_ads",    "custom_ads_bytes",    "custom_ads_uploader",    "custom_ads_currency",    "USD"),
]


def _render_platform_slot(display_name, slug, bytes_key, uploader_key, currency_key, default_currency):
    """Render a single ad platform upload slot with file uploader + currency selectbox."""
    # Custom slot gets a platform name text_input above the uploader row
    if display_name == "Custom":
        st.text_input(
            label="Platform name",
            placeholder="e.g. TikTok Ads, Bing Ads",
            key="custom_platform_name",
            help="Label used in analysis output and charts. Example: TikTok Ads, Bing Ads",
        )

    st.markdown(f"**{display_name}**")

    file_col, ccy_col = st.columns([3, 1])
    with file_col:
        st.file_uploader(
            label="Upload CSV",
            type=["csv"],
            key=uploader_key,
            label_visibility="collapsed",
            help="CSV must include: session_id, campaign_id, clicks, impressions, cost_local, conversion_rate",
        )
    with ccy_col:
        st.selectbox(
            label="Currency",
            options=SUPPORTED_CURRENCIES,
            index=SUPPORTED_CURRENCIES.index(default_currency),
            key=currency_key,
        )

    # per D-04 / UI-SPEC section 4.2: copy bytes into session_state immediately
    if (uf := st.session_state.get(uploader_key)) is not None:
        st.session_state[bytes_key] = uf.getvalue()


# ---------------------------------------------------------------------------
# Ad Platform Data Sources section — 2-column outer grid
# Left: Google Ads + LinkedIn Ads; Right: Meta Ads + Custom
# ---------------------------------------------------------------------------
st.subheader("Ad Platform Data Sources")
st.write("Upload a CSV for each ad platform you want to include. Assign the correct currency for each platform — costs will be normalized to your reporting currency before analysis.")

col_left, col_right = st.columns(2)
with col_left:
    _render_platform_slot(*_PLATFORMS[0])   # Google Ads
    _render_platform_slot(*_PLATFORMS[2])   # LinkedIn Ads
with col_right:
    _render_platform_slot(*_PLATFORMS[1])   # Meta Ads
    _render_platform_slot(*_PLATFORMS[3])   # Custom

# ---------------------------------------------------------------------------
# CRM Data Source section
# ---------------------------------------------------------------------------
st.subheader("CRM Data Source")
st.write("Upload your CRM export CSV. You'll map its columns to the four required fields before the merge proceeds.")
st.file_uploader(
    label="CRM CSV",
    type=["csv"],
    key="crm_uploader",
    help="Any CRM export CSV — you'll map its column names to standard fields below.",
)
# per D-04 / UI-SPEC section 4.2: bytes copy pattern
if (crm_uf := st.session_state.get("crm_uploader")) is not None:
    st.session_state["crm_bytes"] = crm_uf.getvalue()

# ---------------------------------------------------------------------------
# CRM Field Mapping UI — renders only after crm_bytes is set
# per D-05, D-06, D-07, D-08, D-09 / UI-SPEC section 4.4
# ---------------------------------------------------------------------------
if st.session_state["crm_bytes"] is not None:
    import io as _io
    try:
        _crm_columns = list(pd.read_csv(_io.BytesIO(st.session_state["crm_bytes"]), nrows=0).columns)
    except Exception:
        st.error("Could not parse the CRM CSV — verify the file is a valid CSV.")
        st.stop()

    st.markdown("#### Map CRM Columns")
    st.caption("Auto-suggest is based on column name similarity. Review and confirm each field before proceeding.")

    _suggestions = auto_suggest_crm_columns(_crm_columns)

    # per D-08: selectbox keys use the field name string — not a loop index.
    # Keys: crm_map_session_id, crm_map_lead_status, crm_map_projected_value, crm_map_sales_notes
    _help_text = {
        "session_id": "Unique session identifier shared with your ad platform CSVs.",
        "lead_status": "Disposition of the lead (e.g. Qualified, Disqualified, Nurture).",
        "projected_value": "Estimated deal value in your reporting currency.",
        "sales_notes": "Free-text notes from sales reps — the primary signal for the AI.",
    }

    for required_field in REQUIRED_CRM_FIELDS:
        _options = ["— select —"] + _crm_columns
        _suggested = _suggestions.get(required_field)
        _default_index = _options.index(_suggested) if _suggested in _options else 0
        st.selectbox(
            label=required_field,
            options=_options,
            index=_default_index,
            key=f"crm_map_{required_field}",
            help=_help_text[required_field],
        )

    # Optional pass-through columns — exclude already-mapped columns
    _mapped_cols = {st.session_state.get(f"crm_map_{f}") for f in REQUIRED_CRM_FIELDS}
    _extras_options = [c for c in _crm_columns if c not in _mapped_cols]
    st.multiselect(
        label="Pass-through columns (optional)",
        options=_extras_options,
        key="crm_extra_cols",
        help="Extra CRM columns stored as crm_{column_name} in the merged data. Available to future analysis phases.",
    )

    # per D-09: Confirm Mapping button — NOT primary (accent reserved for Run Analysis + Load Demo Data)
    if st.button("Confirm Mapping", key="confirm_crm_mapping"):
        _chosen = {f: st.session_state.get(f"crm_map_{f}") for f in REQUIRED_CRM_FIELDS}
        _missing = [f for f, c in _chosen.items() if not c or c == "— select —"]
        if _missing:
            st.error(f"Required field '{_missing[0]}' is not mapped. Select a column before confirming the mapping.")
        else:
            st.session_state["crm_field_map"] = _chosen
            st.success("Mapping confirmed. Ready to run analysis.")

# ---------------------------------------------------------------------------
# Run Analysis gate — per D-04 / UI-SPEC section 4.3
# ---------------------------------------------------------------------------
_any_ad_bytes = any(st.session_state.get(p[2]) is not None for p in _PLATFORMS)
_gate_ready = (
    _any_ad_bytes
    and st.session_state.get("crm_bytes") is not None
    and st.session_state.get("crm_field_map") is not None
)

if not _gate_ready:
    _missing_items = []
    if not _any_ad_bytes:
        _missing_items.append("at least one ad platform CSV")
    if st.session_state.get("crm_bytes") is None:
        _missing_items.append("CRM CSV")
    if st.session_state.get("crm_bytes") is not None and st.session_state.get("crm_field_map") is None:
        _missing_items.append("CRM field mapping (click Confirm Mapping)")
    if _missing_items:
        st.info("Before Run Analysis, please provide: " + ", ".join(_missing_items) + ".")

if _gate_ready:
    # Build platform_csvs list: (display_name/custom_label, bytes, currency, slug)
    _platform_csvs = []
    for _display_name, _slug, _bytes_key, _uploader_key, _currency_key, _default_currency in _PLATFORMS:
        _byts = st.session_state.get(_bytes_key)
        if _byts is None:
            continue
        _label = _display_name
        if _display_name == "Custom":
            _custom_name = st.session_state.get("custom_platform_name", "").strip()
            if _custom_name:
                _label = _custom_name
        _ccy = st.session_state.get(_currency_key, _default_currency)
        _platform_csvs.append((_label, _byts, _ccy, _slug))

    # Call ingest() once per cache miss — avoids re-ingestion on widget reruns
    if st.session_state["merged_df"] is None:
        try:
            _merged_df = ingest(
                _platform_csvs,
                st.session_state["crm_bytes"],
                st.session_state["crm_field_map"],
                st.session_state["reporting_currency"],
            )
        except ValueError as e:
            _msg = str(e)
            if _msg.lower().startswith("unsupported"):
                st.error(
                    f"Unsupported currency detected. "
                    f"Supported currencies: {', '.join(SUPPORTED_CURRENCIES)}. "
                    f"Update the currency selector for that platform before running analysis."
                )
            elif "column" in _msg.lower() and "conflict" in _msg.lower():
                st.error(
                    "Column name conflict after merge. Ensure your platform CSVs do not share "
                    "non-key column names with your CRM CSV."
                )
            else:
                st.error(f"Merge error: {_msg}")
            st.stop()
        except pd.errors.MergeError:
            st.error(
                "Merge error: duplicate session_id detected in one of your CSVs. "
                "Check that each session appears once per platform file."
            )
            st.stop()

        if len(_merged_df) == 0:
            st.warning(
                "No sessions matched — check that session_id values overlap between "
                "your ad platform CSVs and the CRM CSV."
            )
            st.stop()

        st.session_state["merged_df"] = _merged_df
        st.session_state["campaign_agg"] = compute_campaign_agg(_merged_df)

if st.session_state["merged_df"] is not None:
    merged_df = st.session_state["merged_df"]

    st.subheader("Stitched Dataframe Preview")

    col1, col2 = st.columns(2)
    col1.metric("Sessions", len(merged_df))
    col2.metric("Campaigns", merged_df["campaign_id"].nunique())

    # Dynamic caption reflecting which platforms contributed + reporting currency
    if "platform" in merged_df.columns:
        _platforms_used = sorted(merged_df["platform"].unique().tolist())
        if _platforms_used:
            st.caption(
                f"Sources: {', '.join(_platforms_used)} + CRM "
                f"(reporting currency: {st.session_state['reporting_currency']})"
            )
    else:
        st.caption("Loaded from: data/web_analytics.csv + data/crm_data.csv")

    st.dataframe(merged_df, use_container_width=True, hide_index=True)

    if st.session_state["campaign_agg"] is not None:
        # demo_ready: env DEMO_MODE=1 OR sidebar "Load Demo Data" used — both serve fixture without a key
        demo_ready = (DEMO_MODE or st.session_state.get("demo_mode_active", False)) and llm.client is None
        if llm.client is None and not demo_ready:
            st.info("Enter your OpenAI API key in the sidebar to enable Run Analysis.")
        else:
            # Token gate (Phase 10 D-16)
            _token_count = count_prompt_tokens(st.session_state["campaign_agg"])
            _show_run_analysis = True
            if _token_count >= 60_000:
                if not st.session_state.get("token_warning_confirmed", False):
                    st.warning(
                        f"Your payload is {_token_count:,} tokens — approaching the 128k context "
                        "window. This may affect analysis quality."
                    )
                    if st.button("Continue anyway", key="token_confirm_btn"):
                        st.session_state["token_warning_confirmed"] = True
                        st.rerun()
                    _show_run_analysis = False
                # else: user confirmed — _show_run_analysis stays True

            if _show_run_analysis:
                if st.button("Run Analysis", type="primary"):
                    error_occurred = False
                    with st.status("Analysing campaigns...", expanded=True) as status:
                        status.write("Loading demo analysis..." if demo_ready else "Calling gpt-4o...")
                        try:
                            result = llm._load_fixture() if demo_ready else run_analysis(st.session_state["campaign_agg"])
                        except Exception:
                            status.update(label="Analysis failed", state="error")
                            error_occurred = True
                        if not error_occurred:
                            status.write("Structuring output...")
                            st.session_state["analysis_result"] = result
                            status.update(label="Done ✓", state="complete", expanded=False)
                    if error_occurred:
                        st.error("Analysis failed. Check your OPENAI_API_KEY or retry.")
                        st.stop()

        if st.session_state["analysis_result"] is None:
            st.caption("Click 'Run Analysis' to send aggregated campaign data to gpt-4o for budget recommendations.")

    if st.session_state["analysis_result"] is not None:
        result = st.session_state["analysis_result"]
        st.subheader("Budget Action Results")
        st.markdown(build_exec_summary_html(result.executive_summary), unsafe_allow_html=True)
        st.subheader("Campaign Budget Actions")
        for c in result.campaigns:
            pct_display = f"+{c.percentage_change}%" if c.percentage_change > 0 else f"{c.percentage_change}%"
            label = f"{c.campaign_id} — {c.budget_action.upper()} {pct_display}"
            with st.expander(label, expanded=False):
                st.markdown(
                    f"{_badge_html(c.budget_action)}  &nbsp;  {_pct_html(c.percentage_change)}",
                    unsafe_allow_html=True,
                )
                st.write(c.semantic_reasoning)
                st.caption(
                    f"Confidence: {round(c.confidence * 100)}%  ·  "
                    f"Sessions analysed: {c.evidence_count}"
                )
        st.caption(f"Reasoning grounded in sales-rep qualitative notes — {len(result.campaigns)} campaigns analysed.")

# per UI-SPEC section 4.6: demo-mode caption near Run Analysis area
if st.session_state.get("demo_mode_active") and st.session_state.get("analysis_result") is None:
    st.caption("Using demo data — click Run Analysis to proceed.")
