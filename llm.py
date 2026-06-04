import json
import logging
import os
import time
import tiktoken
from pathlib import Path
from typing import Literal

import pandas as pd
import openai
from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

logger = logging.getLogger(__name__)

_env_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=_env_key) if _env_key else None

MODEL = "gpt-4o-2024-08-06"
MAX_TOKENS = 2000


class CampaignAction(BaseModel):
    campaign_id: str = Field(description="Matches campaign_id from input CSV exactly")
    budget_action: Literal["increase", "pause", "decrease", "insufficient_data"]
    percentage_change: int = Field(
        description="Signed integer -100 to +100. pause=-100, insufficient_data=0."
    )
    semantic_reasoning: str = Field(
        description="One sentence citing specific language from sales notes."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Signal consistency across sessions. 0.0=none, 1.0=unanimous.",
    )
    evidence_count: int = Field(
        description="Echo session_count from input. Do not hallucinate."
    )
    source_platforms: list[str] = Field(
        description=(
            "Echo source_platforms from input data exactly. "
            "List the platform display names (e.g. ['Google Ads', 'Meta Ads']) "
            "that contributed sessions to this campaign."
        )
    )


class AnalysisResult(BaseModel):
    executive_summary: str = Field(
        description="2-3 sentence summary of portfolio health, the single most important action, and which platform is delivering best lead quality per dollar across the portfolio."
    )
    campaigns: list[CampaignAction] = Field(
        description="One CampaignAction per campaign in the input CSV. All campaigns must be included."
    )


SYSTEM_PROMPT = """You are an Autonomous CMO — a senior performance marketer who reads both
quantitative click data AND qualitative sales notes to make decisive, opinionated budget calls.

Rules:
- Sales-rep qualitative notes OVERRIDE click volume when they signal clear disqualification or
  strong qualification. A campaign with high clicks but all "Disqualified" notes is a pause.
- budget_action must be exactly one of: increase, pause, decrease, insufficient_data (snake_case).
- percentage_change: pause = -100, insufficient_data = 0, increase = positive int,
  decrease = negative int. Choose the magnitude based on signal strength.
- evidence_count: echo the session_count column from the input data exactly. Do not invent a number.
- semantic_reasoning: one sentence citing specific language from the sales notes.
- confidence: 0.0–1.0 reflecting how consistent the qualitative signal is across sessions.
- Do not hedge. Make a call for every campaign.
- Cross-platform: when source_platforms lists multiple platforms, compare lead quality per dollar (use {platform}_cost_usd and {platform}_session_count breakdown columns) in semantic_reasoning. Name which platform performs best for this campaign.
- source_platforms: echo the source_platforms value from the input data exactly. Do not invent platform names."""


def count_prompt_tokens(campaign_agg: pd.DataFrame) -> int:
    """Count tokens for system prompt + user message CSV payload.

    Uses o200k_base encoding — the correct encoding for gpt-4o-2024-08-06.
    Mirrors the exact message format in _call_llm() so the count is accurate.
    """
    enc = tiktoken.get_encoding("o200k_base")
    csv_text = campaign_agg.to_csv(index=False)
    user_msg = f"Analyse these campaigns and return your budget decisions:\n\n{csv_text}"
    return len(enc.encode(SYSTEM_PROMPT)) + len(enc.encode(user_msg))


@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    retry=retry_if_not_exception_type(ValueError),
)
def _call_llm(csv_text: str) -> AnalysisResult:
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Analyse these campaigns and return your budget decisions:\n\n{csv_text}",
            },
        ],
        response_format=AnalysisResult,
        max_tokens=MAX_TOKENS,
    )
    message = completion.choices[0].message
    if message.refusal:
        raise ValueError(f"Model refused to analyse: {message.refusal}")
    return message.parsed


def run_analysis(campaign_agg: pd.DataFrame) -> AnalysisResult:
    """Serialize campaign_agg as CSV and send to gpt-4o. Returns a validated AnalysisResult.

    On any OpenAI API error, falls back to fixture and sets
    st.session_state["api_fallback_active"] = True (D-07).
    """
    # per D-01, D-11: fixture path when DEMO_MODE=1 and no live key is present
    if os.environ.get("DEMO_MODE") == "1" and client is None:
        return _load_fixture()
    t0 = time.perf_counter()
    csv_text = campaign_agg.to_csv(index=False)
    _fallback_fired = False
    _err_type = None
    try:
        result = _call_llm(csv_text)
    except openai.OpenAIError as exc:
        _fallback_fired = True
        _err_type = type(exc).__name__
        logger.warning("OpenAI API error — falling back to fixture: %s", exc)
        import streamlit as st
        if hasattr(st, "session_state"):
            st.session_state["api_fallback_active"] = True
        result = _load_fixture()
    try:
        import st_db as _st_db
        _st_db._log_analysis_run(
            run_mode="fixture" if _fallback_fired else "live",
            error_type=_err_type,
            campaign_count=len(result.campaigns),
            latency_ms=int((time.perf_counter() - t0) * 1000),
            api_fallback_active=_fallback_fired,
        )
    except Exception:
        pass
    if _fallback_fired:
        return result
    logger.info(
        "run_analysis completed in %.2fs | campaigns=%d",
        time.perf_counter() - t0,
        len(result.campaigns),
    )
    return result


def _load_fixture() -> AnalysisResult:
    # per D-02: fixture lives at data/fixture_results.json, loaded via model_validate
    fixture_path = Path(__file__).parent / "data" / "fixture_results.json"
    data = json.loads(fixture_path.read_text())
    return AnalysisResult.model_validate(data)
