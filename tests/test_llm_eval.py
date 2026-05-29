"""
Live integration eval for the LLM analysis pipeline.

Calls the real OpenAI API once with the canonical 5-campaign fixture and asserts:
- Directional accuracy: cmp_b2b_search → pause, cmp_competitor_conquest → increase
- evidence_count echoes verified live session counts from compute_campaign_agg
- AI-03 behavioral check: semantic_reasoning for cmp_b2b_search cites sales-note language

Cost: ~$0.01 per run. Expected runtime: 5–10 seconds.
Skipped automatically when OPENAI_API_KEY is unset.
"""

import os
import pytest
from data import load_demo_data, compute_campaign_agg
from llm import run_analysis

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skipping live OpenAI integration eval.",
)

EXPECTED_SESSION_COUNTS = {
    "cmp_b2b_search": 6,
    "cmp_competitor_conquest": 5,
    "cmp_retargeting": 4,
    "cmp_linkedin_outbound": 3,
    "cmp_brand_awareness": 2,
}

EXPECTED_ACTIONS = {
    "cmp_b2b_search": "pause",
    "cmp_competitor_conquest": "increase",
}

# AI-03 behavioral terms — case-insensitive substring match against
# semantic_reasoning for cmp_b2b_search (the all-disqualified campaign).
# The model must cite sales-note language, not just emit schema-valid text.
REASONING_TERMS = [
    "disqualif",     # "disqualified", "disqualification"
    "wrong icp",
    "no budget",
    "wrong fit",
    "not a fit",
]


@pytest.fixture(scope="module")
def live_analysis_result():
    _, _, merged = load_demo_data()
    agg = compute_campaign_agg(merged)
    return run_analysis(agg)


def test_pause_increase_directional_accuracy(live_analysis_result):
    by_id = {c.campaign_id: c for c in live_analysis_result.campaigns}
    for campaign_id, expected_action in EXPECTED_ACTIONS.items():
        action = by_id[campaign_id]
        assert action.budget_action == expected_action, (
            f"{campaign_id}: expected {expected_action!r}, "
            f"got {action.budget_action!r}. Reasoning: {action.semantic_reasoning!r}"
        )


def test_evidence_count_echoes_session_count(live_analysis_result):
    by_id = {c.campaign_id: c for c in live_analysis_result.campaigns}
    for campaign_id, expected_count in EXPECTED_SESSION_COUNTS.items():
        action = by_id[campaign_id]
        assert action.evidence_count == expected_count, (
            f"{campaign_id}: expected evidence_count={expected_count}, "
            f"got {action.evidence_count}"
        )


def test_all_campaigns_returned(live_analysis_result):
    assert len(live_analysis_result.campaigns) == 5
    returned_ids = {c.campaign_id for c in live_analysis_result.campaigns}
    assert returned_ids == set(EXPECTED_SESSION_COUNTS.keys())


def test_executive_summary_nonempty(live_analysis_result):
    assert len(live_analysis_result.executive_summary.strip()) > 20


def test_reasoning_cites_sales_note_language(live_analysis_result):
    b2b = next(c for c in live_analysis_result.campaigns if c.campaign_id == "cmp_b2b_search")
    reasoning_lower = b2b.semantic_reasoning.lower()
    assert any(term in reasoning_lower for term in REASONING_TERMS), (
        f"AI-03 violation: semantic_reasoning for cmp_b2b_search must cite sales-note "
        f"language (one of {REASONING_TERMS}). Got: {b2b.semantic_reasoning!r}"
    )
