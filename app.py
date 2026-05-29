import streamlit as st
import pandas as pd
from data import load_demo_data, compute_campaign_agg
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Performance Plus",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Performance Plus")
st.write("Autonomous Semantic Attribution Engine")

st.markdown("**EXPECTED CSV SCHEMAS (FOR REFERENCE)**")
st.code("session_id, campaign_id, clicks, impressions, cost_usd, conversion_rate", language=None)
st.code("session_id, campaign_id, lead_status, projected_value, sales_notes", language=None)
st.write("Click the button below to load pre-built demo data — no file upload required. The web analytics and CRM CSVs will be stitched on session_id.")

if "merged_df" not in st.session_state:
    st.session_state["merged_df"] = None
if "campaign_agg" not in st.session_state:
    st.session_state["campaign_agg"] = None

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

    st.button("Run Analysis", type="primary", disabled=True)
    st.caption("AI analysis coming in Phase 3.")
