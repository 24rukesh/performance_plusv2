import pathlib
import pandas as pd

_HERE = pathlib.Path(__file__).parent
WEB_CSV = _HERE / "data" / "web_analytics.csv"
CRM_CSV = _HERE / "data" / "crm_data.csv"


def load_demo_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and merge the pre-built demo CSVs.

    Returns:
        (web_df, crm_df, merged_df) — all DataFrames.
        merged_df has 9 columns: session_id, campaign_id, clicks, impressions,
        cost_usd, conversion_rate, lead_status, projected_value, sales_notes.

    Raises:
        FileNotFoundError: if either CSV is missing.
        pd.errors.MergeError: if session_id is duplicated in CRM CSV.

    Returns merged_df with 0 rows (no exception) if session IDs don't overlap.
    """
    web_df = pd.read_csv(WEB_CSV)
    crm_df = pd.read_csv(CRM_CSV)
    merged_df = pd.merge(
        web_df,
        crm_df,
        on=["session_id", "campaign_id"],
        how="inner",
        validate="m:1",
    )
    return web_df, crm_df, merged_df


def compute_campaign_agg(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Roll up session-level data to campaign level.

    Returns DataFrame with columns:
        campaign_id, total_clicks, total_impressions, total_cost_usd,
        avg_conversion_rate, total_projected_value, session_count, sales_notes
    """
    return (
        merged_df
        .groupby("campaign_id")
        .agg(
            total_clicks=("clicks", "sum"),
            total_impressions=("impressions", "sum"),
            total_cost_usd=("cost_usd", "sum"),
            avg_conversion_rate=("conversion_rate", "mean"),
            total_projected_value=("projected_value", "sum"),
            session_count=("session_id", "count"),
            sales_notes=("sales_notes", lambda x: " | ".join(x)),
        )
        .reset_index()
    )
