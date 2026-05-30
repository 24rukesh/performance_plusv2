import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
import llm
from llm import run_analysis, CampaignAction, AnalysisResult


def _minimal_agg_df():
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


def _make_valid_analysis_result():
    return AnalysisResult(
        executive_summary="Pause low-quality campaigns; scale competitor conquest.",
        campaigns=[
            CampaignAction(
                campaign_id="cmp_test",
                budget_action="pause",
                percentage_change=-100,
                semantic_reasoning="Reps flagged 'wrong ICP' across all sessions.",
                confidence=0.95,
                evidence_count=3,
            ),
        ],
    )


def _make_mock_completion(refusal=None, parsed=None):
    completion = MagicMock()
    message = MagicMock()
    message.refusal = refusal
    message.parsed = parsed
    completion.choices[0].message = message
    return completion


@patch("llm.client")
def test_run_analysis_returns_analysis_result(mock_client):
    expected = _make_valid_analysis_result()
    mock_client.beta.chat.completions.parse.return_value = _make_mock_completion(parsed=expected)
    result = run_analysis(_minimal_agg_df())
    assert isinstance(result, AnalysisResult)
    assert result is expected


@patch("llm.client")
def test_run_analysis_calls_parse_with_correct_args(mock_client):
    expected = _make_valid_analysis_result()
    mock_client.beta.chat.completions.parse.return_value = _make_mock_completion(parsed=expected)
    agg_df = _minimal_agg_df()
    run_analysis(agg_df)
    mock_client.beta.chat.completions.parse.assert_called_once()
    kwargs = mock_client.beta.chat.completions.parse.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-2024-08-06"
    assert kwargs["response_format"] is AnalysisResult
    messages = kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert agg_df.to_csv(index=False) in messages[1]["content"]


@patch("llm.client")
def test_run_analysis_raises_on_refusal(mock_client):
    mock_client.beta.chat.completions.parse.return_value = _make_mock_completion(
        refusal="Content policy violation.", parsed=None
    )
    with pytest.raises(ValueError):
        run_analysis(_minimal_agg_df())


def test_budget_action_rejects_invalid_literal():
    with pytest.raises(ValidationError):
        CampaignAction(
            campaign_id="cmp_x",
            budget_action="delete",
            percentage_change=0,
            semantic_reasoning="test",
            confidence=0.5,
            evidence_count=1,
        )


def test_confidence_rejects_out_of_range():
    with pytest.raises(ValidationError):
        CampaignAction(
            campaign_id="cmp_x",
            budget_action="pause",
            percentage_change=-100,
            semantic_reasoning="test",
            confidence=1.5,
            evidence_count=1,
        )
    with pytest.raises(ValidationError):
        CampaignAction(
            campaign_id="cmp_x",
            budget_action="pause",
            percentage_change=-100,
            semantic_reasoning="test",
            confidence=-0.1,
            evidence_count=1,
        )


def test_campaign_action_schema_valid():
    ca = CampaignAction(
        campaign_id="cmp_x",
        budget_action="pause",
        percentage_change=-100,
        semantic_reasoning="Reps flagged budget too small.",
        confidence=0.9,
        evidence_count=6,
    )
    data = ca.model_dump()
    assert data["campaign_id"] == "cmp_x"
    assert data["budget_action"] == "pause"
    assert data["percentage_change"] == -100
    assert data["semantic_reasoning"] == "Reps flagged budget too small."
    assert data["confidence"] == 0.9
    assert data["evidence_count"] == 6
    assert isinstance(data["campaign_id"], str)
    assert isinstance(data["budget_action"], str)
    assert isinstance(data["percentage_change"], int)
    assert isinstance(data["semantic_reasoning"], str)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["evidence_count"], int)


def test_demo_mode_returns_fixture(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setattr("llm.client", None)
    mock_call = MagicMock()
    with patch("llm._call_llm", mock_call):
        result = run_analysis(_minimal_agg_df())
    assert isinstance(result, AnalysisResult)
    assert result.executive_summary
    assert mock_call.call_count == 0


def test_demo_mode_bypassed_when_client_set(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = _make_mock_completion(
        parsed=_make_valid_analysis_result()
    )
    monkeypatch.setattr("llm.client", mock_client)
    mock_fixture = MagicMock()
    with patch("llm._load_fixture", mock_fixture):
        run_analysis(_minimal_agg_df())
    assert mock_client.beta.chat.completions.parse.call_count == 1
    assert mock_fixture.call_count == 0


def test_live_mode_when_demo_not_set(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = _make_mock_completion(
        parsed=_make_valid_analysis_result()
    )
    monkeypatch.setattr("llm.client", mock_client)
    mock_fixture = MagicMock()
    with patch("llm._load_fixture", mock_fixture):
        run_analysis(_minimal_agg_df())
    assert mock_client.beta.chat.completions.parse.call_count == 1
    assert mock_fixture.call_count == 0


def test_fixture_schema():
    result = llm._load_fixture()
    assert isinstance(result, AnalysisResult)
    assert len(result.campaigns) == 5
