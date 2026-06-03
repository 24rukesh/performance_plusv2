import pytest
from llm import AnalysisResult, CampaignAction
from pdf_report import generate_pdf


def _minimal_result() -> AnalysisResult:
    return AnalysisResult(
        executive_summary="Test summary.",
        campaigns=[
            CampaignAction(
                campaign_id="cmp_test",
                budget_action="increase",
                percentage_change=25,
                semantic_reasoning="Strong lead quality.",
                confidence=0.9,
                evidence_count=5,
                source_platforms=["Google Ads"],
            )
        ],
    )


def _meta() -> dict:
    return {
        "date": "2026-06-03",
        "platforms_used": "Google Ads",
        "session_count": 5,
        "reporting_currency": "INR",
    }


def test_generate_pdf_returns_bytes():
    result = generate_pdf(_minimal_result(), _meta())
    assert isinstance(result, bytes)
    assert len(result) > 500


def test_generate_pdf_magic_bytes():
    result = generate_pdf(_minimal_result(), _meta())
    assert result[:4] == b"%PDF"


def test_generate_pdf_multiple_campaigns():
    r = AnalysisResult(
        executive_summary="Multi-campaign test.",
        campaigns=[
            CampaignAction(
                campaign_id=f"cmp_{i}",
                budget_action=action,
                percentage_change=pct,
                semantic_reasoning="Test reasoning.",
                confidence=0.8,
                evidence_count=3,
                source_platforms=["Google Ads"],
            )
            for i, (action, pct) in enumerate([("increase", 20), ("pause", 0), ("decrease", -15)])
        ],
    )
    result = generate_pdf(r, _meta())
    assert isinstance(result, bytes)


def test_generate_pdf_empty_source_platforms():
    r = AnalysisResult(
        executive_summary="Empty platforms test.",
        campaigns=[
            CampaignAction(
                campaign_id="cmp_empty",
                budget_action="insufficient_data",
                percentage_change=0,
                semantic_reasoning="No data.",
                confidence=0.1,
                evidence_count=1,
                source_platforms=[],
            )
        ],
    )
    result = generate_pdf(r, _meta())
    assert isinstance(result, bytes)


def test_generate_pdf_meta_keys():
    meta = {
        "date": "2026-06-03",
        "platforms_used": "Google Ads, Meta Ads",
        "session_count": 42,
        "reporting_currency": "USD",
    }
    result = generate_pdf(_minimal_result(), meta)
    assert isinstance(result, bytes)
    assert len(result) > 500
