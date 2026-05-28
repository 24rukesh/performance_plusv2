import pathlib
import pytest
import pandas as pd
from data import load_demo_data, compute_campaign_agg


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
    ]
