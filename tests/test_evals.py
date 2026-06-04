"""test_evals.py — AI-SPEC §5 evaluation dimension tests.

Covers:
  Dimension 1: Fallback trigger selectivity (openai.OpenAIError subclasses trigger fallback;
               ValueError does not)
  Dimension 3: Fixture schema compliance (_load_fixture() returns valid AnalysisResult)
  Dimension 7: Budget action decisiveness (fixture campaigns with evidence get directional actions)
"""
import sys
import pytest
import pandas as pd
import openai
from unittest.mock import MagicMock, patch

from llm import run_analysis, _load_fixture, AnalysisResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_agg_df() -> pd.DataFrame:
    """Minimal campaign_agg DataFrame for use in Dimension 1 tests."""
    return pd.DataFrame([{
        "campaign_id": "cmp_test",
        "total_clicks": 100,
        "total_impressions": 1000,
        "total_cost_usd": 50.0,
        "avg_conversion_rate": 0.05,
        "total_projected_value": 500.0,
        "session_count": 3,
        "sales_notes": "Good leads. | Strong fit.",
    }])


def _make_openai_exc(exc_class):
    """Construct an instance of the given openai exception class.

    RateLimitError and AuthenticationError take (message, *, response, body).
    APIConnectionError takes (*, request) — uses __new__ so no positional message needed.
    """
    if exc_class is openai.APIConnectionError:
        return exc_class(request=MagicMock())
    return exc_class("mock error", response=MagicMock(), body={})


# ---------------------------------------------------------------------------
# Dimension 1: Fallback trigger selectivity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("exc_class", [
    openai.RateLimitError,
    openai.AuthenticationError,
    openai.APIConnectionError,
])
def test_openai_error_triggers_fallback(exc_class, monkeypatch):
    """D1-PASS: OpenAI SDK errors trigger fallback and set api_fallback_active=True."""
    # Inject fake streamlit module so the local import inside the except branch resolves
    mock_st = MagicMock()
    mock_st.session_state = {}
    monkeypatch.setitem(sys.modules, "streamlit", mock_st)
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setattr("llm.client", MagicMock())

    exc = _make_openai_exc(exc_class)

    with patch("llm._call_llm", side_effect=exc):
        result = run_analysis(_minimal_agg_df())

    # Must return a valid AnalysisResult (the fixture)
    assert isinstance(result, AnalysisResult), (
        f"Expected AnalysisResult, got {type(result)}"
    )
    # Must set api_fallback_active=True in the injected session state
    assert mock_st.session_state.get("api_fallback_active") is True, (
        f"api_fallback_active not set for {exc_class.__name__}"
    )


def test_value_error_does_not_trigger_fallback(monkeypatch):
    """D1-PASS: ValueError propagates unhandled — does NOT trigger fallback."""
    mock_st = MagicMock()
    mock_st.session_state = {}
    monkeypatch.setitem(sys.modules, "streamlit", mock_st)
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setattr("llm.client", MagicMock())

    with patch("llm._call_llm", side_effect=ValueError("bad input")):
        with pytest.raises(ValueError, match="bad input"):
            run_analysis(_minimal_agg_df())

    # api_fallback_active must NOT be set (ValueError never enters the except branch)
    assert mock_st.session_state.get("api_fallback_active") is not True


# ---------------------------------------------------------------------------
# Dimension 3: Fixture schema compliance
# ---------------------------------------------------------------------------

def test_fixture_schema_compliance():
    """D3-PASS: _load_fixture() returns a valid AnalysisResult with >= 3 campaigns,
    all fields valid, at least one directional action, and all evidence_count >= 1.
    """
    result = _load_fixture()

    assert isinstance(result, AnalysisResult), (
        f"Expected AnalysisResult, got {type(result)}"
    )
    assert isinstance(result.executive_summary, str) and len(result.executive_summary) > 0, (
        "executive_summary must be a non-empty string"
    )
    assert len(result.campaigns) >= 3, (
        f"Fixture must have >= 3 campaigns, got {len(result.campaigns)}"
    )

    # At least one campaign must have a directional (non-insufficient_data) action
    directional_actions = {
        c.budget_action for c in result.campaigns
        if c.budget_action != "insufficient_data"
    }
    assert len(directional_actions) >= 1, (
        "Fixture must have at least one directional budget_action "
        "(increase/pause/decrease) — not all insufficient_data"
    )

    for c in result.campaigns:
        assert c.evidence_count >= 1, (
            f"Campaign {c.campaign_id}: evidence_count must be >= 1, got {c.evidence_count}"
        )
        assert 0.0 <= c.confidence <= 1.0, (
            f"Campaign {c.campaign_id}: confidence {c.confidence} not in [0.0, 1.0]"
        )
        assert len(c.source_platforms) >= 1, (
            f"Campaign {c.campaign_id}: source_platforms must be non-empty"
        )


# ---------------------------------------------------------------------------
# Dimension 7: Budget action decisiveness on fixture
# ---------------------------------------------------------------------------

def test_budget_action_decisiveness_on_fixture():
    """D7-PASS: For every fixture campaign with evidence_count > 0,
    budget_action is directional, percentage_change != 0, and confidence >= 0.5.
    """
    result = _load_fixture()

    campaigns_with_evidence = [c for c in result.campaigns if c.evidence_count > 0]
    assert len(campaigns_with_evidence) >= 1, (
        "Fixture must have at least one campaign with evidence_count > 0 to test decisiveness"
    )

    for c in campaigns_with_evidence:
        assert c.budget_action != "insufficient_data", (
            f"Campaign {c.campaign_id} has evidence_count={c.evidence_count} "
            f"but returned budget_action='insufficient_data'"
        )
        assert c.percentage_change != 0, (
            f"Campaign {c.campaign_id} has evidence_count={c.evidence_count} "
            f"but percentage_change=0 (non-committal)"
        )
        assert c.confidence >= 0.5, (
            f"Campaign {c.campaign_id} has evidence_count={c.evidence_count} "
            f"but confidence={c.confidence} < 0.5"
        )
