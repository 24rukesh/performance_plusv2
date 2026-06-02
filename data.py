import pathlib
import pandas as pd

_HERE = pathlib.Path(__file__).parent
WEB_CSV = _HERE / "data" / "web_analytics.csv"
CRM_CSV = _HERE / "data" / "crm_data.csv"

# Authoritative slug-to-display-name mapping — mirrors app.py _PLATFORMS entries.
# Do NOT derive via .replace("_", " ").title() — "linkedin_ads" yields "Linkedin Ads"
# (lowercase i), but the correct display name is "LinkedIn Ads" (capital I).
SLUG_TO_DISPLAY: dict[str, str] = {
    "google_ads": "Google Ads",
    "meta_ads": "Meta Ads",
    "linkedin_ads": "LinkedIn Ads",
    "custom_ads": "Custom",
}


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


def _detect_slugs(merged_df: pd.DataFrame) -> list[str]:
    """Return platform slugs detected from source-prefixed _clicks columns.

    Cross-validates against platform display names in merged_df["platform"] to
    avoid false positives from non-standard columns (e.g. 'paid_clicks' from
    a Google Ads CSV would yield candidate 'google_ads_paid', not a valid slug).

    Returns empty list for legacy single-source DataFrames (no 'platform' column).
    """
    if "platform" not in merged_df.columns:
        return []

    platform_display_names = set(merged_df["platform"].unique())
    slugs = []
    for col in merged_df.columns:
        if col.endswith("_clicks") and col != "clicks":
            candidate = col[: -len("_clicks")]  # strip "_clicks"
            display = SLUG_TO_DISPLAY.get(candidate)
            if display is not None and display in platform_display_names:
                slugs.append(candidate)
    return slugs


def _compute_platform_pivot(merged_df: pd.DataFrame, slugs: list[str]) -> pd.DataFrame:
    """Return per-platform cost_usd and session_count columns indexed by campaign_id.

    Columns produced: {slug}_cost_usd and {slug}_session_count for each slug.
    fill_value=0 ensures platforms absent from a campaign get 0, not NaN.
    """
    display_to_slug = {SLUG_TO_DISPLAY[s]: s for s in slugs if s in SLUG_TO_DISPLAY}

    df = merged_df.copy()
    df["_slug"] = df["platform"].map(display_to_slug)

    platform_grp = (
        df.groupby(["campaign_id", "_slug"])
        .agg(
            _cost=("cost_usd", "sum"),
            _count=("session_id", "count"),
        )
        .reset_index()
    )

    cost_piv = platform_grp.pivot_table(
        index="campaign_id", columns="_slug", values="_cost", fill_value=0
    ).reset_index()
    cost_piv.columns.name = None
    for s in slugs:
        if s in cost_piv.columns:
            cost_piv.rename(columns={s: f"{s}_cost_usd"}, inplace=True)

    count_piv = platform_grp.pivot_table(
        index="campaign_id", columns="_slug", values="_count", fill_value=0
    ).reset_index()
    count_piv.columns.name = None
    for s in slugs:
        if s in count_piv.columns:
            count_piv.rename(columns={s: f"{s}_session_count"}, inplace=True)

    return cost_piv.merge(count_piv, on="campaign_id", how="left")


def _compute_source_platforms(agg_df: pd.DataFrame, slugs: list[str]) -> pd.Series:
    """Return pipe-delimited platform display names for campaigns with sessions > 0.

    Uses SLUG_TO_DISPLAY for accurate display names (avoids linkedin_ads .title() mismatch).
    """
    def get_platforms(row: pd.Series) -> str:
        contributing = [
            SLUG_TO_DISPLAY[s]
            for s in slugs
            if s in SLUG_TO_DISPLAY and row.get(f"{s}_session_count", 0) > 0
        ]
        return "|".join(contributing)

    return agg_df.apply(get_platforms, axis=1)


def compute_campaign_agg(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Roll up session-level data to campaign level.

    Returns DataFrame with columns:
        campaign_id, total_clicks, total_impressions, total_cost_usd,
        avg_conversion_rate, total_projected_value, session_count, sales_notes,
        source_platforms
        [+ {slug}_cost_usd, {slug}_session_count columns for multi-source DataFrames]

    Legacy path (no 'platform' column): source_platforms is always "".
    Multi-source path: per-platform breakdown columns added; source_platforms
    is a pipe-delimited string of contributing platform display names.
    """
    slugs = _detect_slugs(merged_df)
    is_multi_source = len(slugs) > 0

    # CRM enrichment (both paths): append crm_-prefixed extra columns to sales_notes
    crm_extra = [c for c in merged_df.columns if c.startswith("crm_")]
    if crm_extra:
        def enrich_notes(row: pd.Series) -> str:
            parts = [row["sales_notes"]]
            for col in crm_extra:
                label = col[4:]  # strip "crm_"
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    parts.append(f"{label}: {val}")
            return " | ".join(parts)

        merged_df = merged_df.copy()
        merged_df["sales_notes"] = merged_df.apply(enrich_notes, axis=1)

    # Multi-source only: synthesise unified columns from source-prefixed columns
    if is_multi_source:
        all_click_cols = [c for c in merged_df.columns if c.endswith("_clicks") and c != "clicks"]
        all_impr_cols = [c for c in merged_df.columns if c.endswith("_impressions") and c != "impressions"]
        all_conv_cols = [c for c in merged_df.columns if c.endswith("_conversion_rate") and c != "conversion_rate"]
        if all_click_cols:
            merged_df = merged_df.copy() if not crm_extra else merged_df  # already copied if crm_extra
            if crm_extra:
                pass  # already a copy
            else:
                merged_df = merged_df.copy()
            merged_df["clicks"] = merged_df[all_click_cols].sum(axis=1, skipna=True)
            merged_df["impressions"] = merged_df[all_impr_cols].sum(axis=1, skipna=True)
            merged_df["conversion_rate"] = merged_df[all_conv_cols].mean(axis=1, skipna=True)

    # Core groupby aggregation (unchanged for both paths)
    agg_df = (
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

    if is_multi_source:
        # Merge per-platform pivot and compute source_platforms
        pivot_df = _compute_platform_pivot(merged_df, slugs)
        agg_df = agg_df.merge(pivot_df, on="campaign_id", how="left")
        agg_df["source_platforms"] = _compute_source_platforms(agg_df, slugs)
    else:
        # Legacy path: always add source_platforms as empty string
        agg_df["source_platforms"] = ""

    return agg_df
