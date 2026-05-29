import os
import pytest
from llm import CampaignAction, AnalysisResult
from ui_helpers import _badge_html, _pct_html, build_results_table_html, build_exec_summary_html

os.environ.setdefault("OPENAI_API_KEY", "sk-dummy")


def _one_campaign_result(**overrides):
    defaults = dict(
        campaign_id="cmp_test",
        budget_action="pause",
        percentage_change=-100,
        semantic_reasoning="Reps flagged disqualified leads.",
        confidence=0.87,
        evidence_count=6,
    )
    defaults.update(overrides)
    return AnalysisResult(
        executive_summary="Pause two campaigns; scale one.",
        campaigns=[CampaignAction(**defaults)],
    )


def test_badge_html_colors_and_labels():
    html_increase = _badge_html("increase")
    assert "#09ab3b" in html_increase
    assert "#ffffff" in html_increase
    assert "INCREASE" in html_increase

    html_pause = _badge_html("pause")
    assert "#ff2b2b" in html_pause
    assert "#ffffff" in html_pause
    assert "PAUSE" in html_pause

    html_decrease = _badge_html("decrease")
    assert "#faca2b" in html_decrease
    assert "#262730" in html_decrease
    assert "DECREASE" in html_decrease

    html_insufficient = _badge_html("insufficient_data")
    assert "#808495" in html_insufficient
    assert "#ffffff" in html_insufficient
    assert "INSUFFICIENT DATA" in html_insufficient
    assert "INSUFFICIENT_DATA" not in html_insufficient


def test_pct_html_formatting():
    html_pos = _pct_html(25)
    assert "+25%" in html_pos
    assert "#09ab3b" in html_pos

    html_neg = _pct_html(-100)
    assert "-100%" in html_neg
    assert "#ff2b2b" in html_neg

    html_zero = _pct_html(0)
    assert "0%" in html_zero
    assert "#808495" in html_zero


def test_exec_summary_html_structure():
    html = build_exec_summary_html("Pause two campaigns.")
    assert "border-left:4px solid #f63366" in html
    assert "background:#f0f2f6" in html
    assert "<strong>This week:</strong>" in html
    assert "Pause two campaigns." in html


def test_results_table_html_columns():
    result = _one_campaign_result()
    html = build_results_table_html(result)
    assert "<table" in html
    assert "</table>" in html
    assert "campaign_id" in html
    assert "action" in html
    assert "budget_change_%" in html
    assert "reasoning" in html
    assert "confidence" in html
    assert "sessions" in html
    assert "cmp_test" in html
    assert "IBM Plex Mono" in html


def test_results_table_row_renders_badge_pct_confidence():
    result = _one_campaign_result(
        budget_action="pause",
        percentage_change=-100,
        confidence=0.87,
        evidence_count=6,
    )
    html = build_results_table_html(result)
    assert "PAUSE" in html
    assert "#ff2b2b" in html
    assert "-100%" in html
    assert "87%" in html
    assert ">6<" in html
