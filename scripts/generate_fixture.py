"""
One-time helper: run a real gpt-4o call against the demo CSVs and write the result
to data/fixture_results.json so DEMO_MODE=1 can serve cached results.

Usage:
    export OPENAI_API_KEY=sk-...
    unset DEMO_MODE
    uv run python scripts/generate_fixture.py

Expected output: Fixture written to data/fixture_results.json (5 campaigns)
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from data import load_demo_data, compute_campaign_agg  # noqa: E402
from llm import run_analysis  # noqa: E402

if __name__ == "__main__":
    _, _, merged_df = load_demo_data()
    campaign_agg = compute_campaign_agg(merged_df)

    result = run_analysis(campaign_agg)

    fixture_path = REPO_ROOT / "data" / "fixture_results.json"
    fixture_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2))

    print(f"Fixture written to {fixture_path} ({len(result.campaigns)} campaigns)")
