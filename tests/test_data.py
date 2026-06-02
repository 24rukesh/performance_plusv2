import pathlib
import pytest
import pandas as pd
from data import load_demo_data, compute_campaign_agg


def _multi_source_merged_df() -> pd.DataFrame:
    """Minimal multi-source merged_df with two platforms for testing compute_campaign_agg."""
    return pd.DataFrame([
        {
            "session_id": "s1", "campaign_id": "cmp_a", "platform": "Google Ads",
            "cost_usd": 10.0, "google_ads_clicks": 100.0, "google_ads_impressions": 1000.0,
            "google_ads_conversion_rate": 0.05, "meta_ads_clicks": None,
            "meta_ads_impressions": None, "meta_ads_conversion_rate": None,
            "lead_status": "Qualified", "projected_value": 1000.0, "sales_notes": "Good lead",
        },
        {
            "session_id": "s2", "campaign_id": "cmp_a", "platform": "Meta Ads",
            "cost_usd": 5.0, "google_ads_clicks": None, "google_ads_impressions": None,
            "google_ads_conversion_rate": None, "meta_ads_clicks": 30.0,
            "meta_ads_impressions": 300.0, "meta_ads_conversion_rate": 0.07,
            "lead_status": "Disqualified", "projected_value": 0.0, "sales_notes": "Wrong ICP",
        },
        {
            "session_id": "s3", "campaign_id": "cmp_b", "platform": "Google Ads",
            "cost_usd": 8.0, "google_ads_clicks": 50.0, "google_ads_impressions": 500.0,
            "google_ads_conversion_rate": 0.03, "meta_ads_clicks": None,
            "meta_ads_impressions": None, "meta_ads_conversion_rate": None,
            "lead_status": "Qualified", "projected_value": 500.0, "sales_notes": "Strong fit",
        },
    ])


def test_load_demo_data_returns_correct_shape():
    web_df, crm_df, merged_df = load_demo_data()
    assert merged_df.shape == (20, 9)
    expected_cols = [
        "session_id", "campaign_id", "clicks", "impressions",
        "cost_usd", "conversion_rate", "lead_status", "projected_value", "sales_notes",
    ]
    assert list(merged_df.columns) == expected_cols


def test_merge_produces_no_suffix_columns():
    _, _, merged_df = load_demo_data()
    assert "campaign_id_x" not in merged_df.columns
    assert "campaign_id_y" not in merged_df.columns


def test_merge_error_on_duplicate_session_id(tmp_path):
    web_df = pd.DataFrame([
        {"session_id": "sess_001", "campaign_id": "cmp_a", "clicks": 10,
         "impressions": 100, "cost_usd": 5.0, "conversion_rate": 0.01},
    ])
    crm_df = pd.DataFrame([
        {"session_id": "sess_001", "campaign_id": "cmp_a", "lead_status": "Qualified",
         "projected_value": 100.0, "sales_notes": "Good lead."},
        {"session_id": "sess_001", "campaign_id": "cmp_a", "lead_status": "Qualified",
         "projected_value": 100.0, "sales_notes": "Duplicate."},
    ])
    with pytest.raises(pd.errors.MergeError):
        pd.merge(web_df, crm_df, on=["session_id", "campaign_id"],
                 how="inner", validate="m:1")


def test_load_demo_data_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("data.WEB_CSV", tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError):
        load_demo_data()


def test_compute_campaign_agg_returns_five_campaigns():
    _, _, merged_df = load_demo_data()
    agg_df = compute_campaign_agg(merged_df)
    assert len(agg_df) == 5
    assert set(agg_df["campaign_id"]) == {
        "cmp_b2b_search", "cmp_competitor_conquest", "cmp_retargeting",
        "cmp_linkedin_outbound", "cmp_brand_awareness",
    }
    assert list(agg_df.columns) == [
        "campaign_id", "total_clicks", "total_impressions", "total_cost_usd",
        "avg_conversion_rate", "total_projected_value", "session_count", "sales_notes",
        "source_platforms",
    ]


def test_compute_campaign_agg_multi_source_breakdown_columns():
    """Multi-source path produces per-platform cost and session count columns."""
    agg_df = compute_campaign_agg(_multi_source_merged_df())
    assert "google_ads_cost_usd" in agg_df.columns
    assert "meta_ads_cost_usd" in agg_df.columns
    assert "google_ads_session_count" in agg_df.columns
    assert "meta_ads_session_count" in agg_df.columns
    cmp_a = agg_df[agg_df["campaign_id"] == "cmp_a"].iloc[0]
    assert cmp_a["google_ads_cost_usd"] == pytest.approx(10.0)
    assert cmp_a["meta_ads_cost_usd"] == pytest.approx(5.0)
    assert cmp_a["google_ads_session_count"] == 1
    assert cmp_a["meta_ads_session_count"] == 1


def test_compute_campaign_agg_source_platforms_column():
    """source_platforms column is present and pipe-delimited with contributing display names."""
    agg_df = compute_campaign_agg(_multi_source_merged_df())
    assert "source_platforms" in agg_df.columns
    cmp_a = agg_df[agg_df["campaign_id"] == "cmp_a"].iloc[0]
    assert "Google Ads" in cmp_a["source_platforms"]
    assert "Meta Ads" in cmp_a["source_platforms"]
    cmp_b = agg_df[agg_df["campaign_id"] == "cmp_b"].iloc[0]
    assert cmp_b["source_platforms"] == "Google Ads"


def test_compute_campaign_agg_legacy_path_unchanged():
    """Legacy single-source path produces source_platforms column with all empty strings."""
    _, _, merged_df = load_demo_data()
    agg_df = compute_campaign_agg(merged_df)
    assert "source_platforms" in agg_df.columns
    assert all(v == "" for v in agg_df["source_platforms"])


def test_compute_campaign_agg_crm_extra_cols_in_sales_notes():
    """crm_-prefixed extra columns are appended to sales_notes string per D-06."""
    df = _multi_source_merged_df()
    df["crm_deal_stage"] = "Proposal"
    agg_df = compute_campaign_agg(df)
    # Every campaign's sales_notes should contain "deal_stage: Proposal"
    assert all("deal_stage: Proposal" in notes for notes in agg_df["sales_notes"])
