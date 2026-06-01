import os

import streamlit as st
import pandas as pd
from openai import OpenAI
from data import load_demo_data, compute_campaign_agg
from dotenv import load_dotenv
import llm
from llm import run_analysis
from ui_helpers import _badge_html, _pct_html, build_exec_summary_html

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

# per D-05: info banner renders in main column above title when DEMO_MODE=1
if DEMO_MODE:
    st.info("ℹ️ Running in demo mode — cached results, no live API call")

st.markdown(BRANDED_HEADER_HTML, unsafe_allow_html=True)

st.markdown("**EXPECTED CSV SCHEMAS (FOR REFERENCE)**")
st.code("session_id, campaign_id, clicks, impressions, cost_usd, conversion_rate", language=None)
st.code("session_id, campaign_id, lead_status, projected_value, sales_notes", language=None)
st.write("Click the button below to load pre-built demo data — no file upload required. The web analytics and CRM CSVs will be stitched on session_id.")

if "merged_df" not in st.session_state:
    st.session_state["merged_df"] = None
if "campaign_agg" not in st.session_state:
    st.session_state["campaign_agg"] = None
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if st.button("Load Demo Data", type="primary"):
    try:
        web_df, crm_df, merged_df = load_demo_data()
    except FileNotFoundError:
        st.error("Demo data files not found. Run: python data_generator.py")
        st.stop()
    except pd.errors.MergeError:
        st.error(
            "Data error: duplicate session_id detected in CRM data. "
            "Check data/crm_data.csv."
        )
        st.stop()

    if len(merged_df) == 0:
        st.warning("No sessions matched — check session_id overlap between CSVs.")
        st.stop()

    st.session_state["merged_df"] = merged_df
    st.session_state["campaign_agg"] = compute_campaign_agg(merged_df)

st.caption("Demo mode uses pre-built mock CSVs from data/ directory.")

if st.session_state["merged_df"] is not None:
    merged_df = st.session_state["merged_df"]

    st.subheader("Stitched Dataframe Preview")

    col1, col2 = st.columns(2)
    col1.metric("Sessions", len(merged_df))
    col2.metric("Campaigns", merged_df["campaign_id"].nunique())

    st.caption("Loaded from: data/web_analytics.csv + data/crm_data.csv")

    st.dataframe(merged_df, use_container_width=True, hide_index=True)

    if st.session_state["campaign_agg"] is not None:
        # per D-11: DEMO_MODE with no key is allowed; key presence takes precedence over fixture
        demo_ready = DEMO_MODE and llm.client is None
        if llm.client is None and not demo_ready:
            st.info("Enter your OpenAI API key in the sidebar to enable Run Analysis.")
        elif st.button("Run Analysis", type="primary"):
            error_occurred = False
            with st.status("Analysing campaigns...", expanded=True) as status:
                status.write("Calling gpt-4o...")
                try:
                    result = run_analysis(st.session_state["campaign_agg"])
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
