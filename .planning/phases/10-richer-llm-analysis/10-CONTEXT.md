# Phase 10: Richer LLM Analysis - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend `llm.py`, `data.py`, and `app.py` so that gpt-4o receives multi-source campaign data and returns richer, cross-platform-aware budget recommendations.

Specifically:
1. **`compute_campaign_agg` extension** — remove the Phase 9 bridge block in `app.py` (commit `5bbdc71`, lines 362–371) and extend `data.py:compute_campaign_agg()` to natively produce per-platform breakdown columns (`{platform_slug}_cost_usd`, `{platform_slug}_session_count`) alongside existing unified totals, plus a pre-computed `source_platforms` column.
2. **Pydantic schema update** — add `source_platforms: list[str]` to `CampaignAction` in `llm.py`.
3. **System prompt update** — add cross-platform comparison rule and update `executive_summary` field description.
4. **Token preflight** — add tiktoken token-count check before every `_call_llm()` invocation; surface warning gate in `app.py` when payload ≥ 60k tokens.
5. **Extra CRM columns** — when `crm_`-prefixed pass-through columns exist in `merged_df`, append their values to the `sales_notes` aggregation string in `compute_campaign_agg`.

**In scope:** `data.py`, `llm.py`, `app.py` (bridge removal + token gate UI), `tests/test_data.py` (new agg assertions), `tests/test_llm.py` (schema + prompt assertions).

**Out of scope:** Charts, filters, side-by-side comparison (Phase 11). Save/load to Postgres (Phase 12). New platform upload slots or FX changes (Phase 9 complete). Live FX rate API (v4+).

</domain>

<decisions>
## Implementation Decisions

### compute_campaign_agg Extension

- **D-01:** Keep one row per campaign (do NOT pivot to campaign+platform rows). Add per-platform breakdown columns alongside existing unified totals.
- **D-02:** Per-platform breakdown columns: `{platform_slug}_cost_usd` and `{platform_slug}_session_count` only (e.g., `google_ads_cost_usd`, `google_ads_session_count`, `meta_ads_cost_usd`, `meta_ads_session_count`). Unified `total_clicks`, `total_impressions`, `avg_conversion_rate`, `total_cost_usd`, `total_projected_value`, `session_count` remain unchanged.
- **D-03:** `source_platforms` column — Python pre-computes which platforms contributed sessions to each campaign (i.e., where `{platform_slug}_session_count > 0`). Store as a pipe-delimited string (e.g., `"Google Ads|Meta Ads"`) in the aggregation CSV so the LLM can echo it verbatim. Same echo pattern as `evidence_count` ↔ `session_count`.
- **D-04:** The Phase 9 bridge block in `app.py` (lines 362–371) is deleted entirely once `compute_campaign_agg` handles source-prefixed columns natively. No other `app.py` logic changes for the aggregation step.
- **D-05:** Per-platform breakdown columns are derived from source-prefixed columns in `merged_df` (e.g., `google_ads_cost_usd`, `meta_ads_session_count`). The function detects these dynamically (regex or endswith pattern matching) — no hardcoded platform list in `data.py`.

### Extra CRM Columns in Prompt

- **D-06:** Optional `crm_`-prefixed pass-through columns (if present in `merged_df`) are concatenated into the `sales_notes` aggregation string in `compute_campaign_agg`. Format: existing sales notes first, then each extra column appended as `{field_label}: {value}` separated by ` | `. Example: `"Strong interest in enterprise plan | deal_stage: Proposal | company_size: 200+"`. Zero schema change to `CampaignAction`.

### Pydantic Schema Update

- **D-07:** Add `source_platforms: list[str]` to `CampaignAction` with description: `"Echo source_platforms from input data exactly. List the platform display names (e.g. ['Google Ads', 'Meta Ads']) that contributed sessions to this campaign."`.
- **D-08:** No other schema changes. `executive_summary`, `budget_action`, `percentage_change`, `semantic_reasoning`, `confidence`, `evidence_count` fields stay unchanged.

### System Prompt Changes

- **D-09:** Add one bullet to the existing `SYSTEM_PROMPT` Rules list: `"- Cross-platform: when source_platforms lists multiple platforms, compare lead quality per dollar (use {platform}_cost_usd and {platform}_session_count breakdown columns) in semantic_reasoning. Name which platform performs best for this campaign."`.
- **D-10:** Update `executive_summary` Field description to: `"2-3 sentence summary of portfolio health, the single most important action, and which platform is delivering best lead quality per dollar across the portfolio."`.
- **D-11:** Add one bullet to SYSTEM_PROMPT for `source_platforms`: `"- source_platforms: echo the source_platforms value from the input data exactly. Do not invent platform names."`.

### Token Preflight (AGENT-03)

- **D-12:** Token count is computed with `tiktoken` using the `cl100k_base` encoding (correct encoding for gpt-4o). Count includes both the system prompt tokens + the user message CSV text. Computation happens inside `run_analysis()` before `_call_llm()` is called.
- **D-13:** Threshold: **60,000 tokens** (as specified in AGENT-03). No other threshold.
- **D-14:** `run_analysis()` does NOT raise or return anything special when the threshold is exceeded — it always proceeds with the API call regardless of token count. The warning gate is the UI's responsibility.
- **D-15:** Token count is returned as part of the result context so `app.py` can display it. Approach: `run_analysis()` returns a tuple `(AnalysisResult, token_count: int)` OR `token_count` is passed back via a module-level variable. **Claude decides the cleanest pattern** — returning a tuple is preferred to avoid module-level state.
- **D-16:** In `app.py`, before the `Run Analysis` button fires the API call, a separate `_token_count` is computed (by calling a new `count_prompt_tokens(campaign_agg)` helper in `llm.py`) and compared to 60,000. If ≥ 60k: `st.warning(f"Your payload is {_token_count:,} tokens — approaching the 128k context window. This may affect analysis quality.")` + a "Continue anyway" `st.button` gates the call. If < 60k: proceed normally with the existing `Run Analysis` button.

### Claude's Discretion

- Whether `run_analysis` returns `(AnalysisResult, int)` tuple or delegates token counting to a separate `count_prompt_tokens()` helper that `app.py` calls independently — prefer the separate helper to keep `run_analysis()` signature stable (app.py already calls it directly).
- Exact column detection pattern for source-prefixed columns in `compute_campaign_agg` (regex vs. endswith) — endswith is simpler and sufficient.
- Whether platform slug is derived from the `platform` column values or the source-prefix column names — use source-prefix column names (already in the DataFrame) rather than the `platform` string column to avoid slug/display-name mismatch.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing code (read before touching)
- `llm.py` — `CampaignAction`, `AnalysisResult`, `SYSTEM_PROMPT`, `_call_llm()`, `run_analysis()` — Phase 10 extends all of these
- `data.py` — `compute_campaign_agg()` — Phase 10 extends this function; signature stays the same (`merged_df: pd.DataFrame → pd.DataFrame`)
- `app.py` lines 359–373 — Phase 9 bridge block to DELETE; lines 402–418 — Run Analysis flow where token gate UI is inserted
- `ingest.py` — `SUPPORTED_CURRENCIES`, source-prefix renaming logic (D-14 of Phase 9 CONTEXT) — confirms source-prefixed column names follow `{platform_slug}_{original_col}` pattern

### Requirements
- `.planning/REQUIREMENTS.md` — AGENT-01, AGENT-02, AGENT-03

### Prior phase decisions
- `.planning/phases/09-multi-source-ingestion/09-CONTEXT.md` — D-07 (extra CRM cols deferred to Phase 10), D-14 (source-prefix naming convention), D-15 (`platform` and `currency_code` columns in merged_df)
- `.planning/STATE.md` — Pending Todo: "Phase 10 must extend `compute_campaign_agg` in data.py to natively handle source-prefixed numeric columns" (authoritative description of the bridge-removal task)

### Test regression net
- `tests/test_ingest.py` — 24 tests covering ingest.py; run after any change to `compute_campaign_agg` to verify the upstream DataFrame contract is preserved
- `tests/test_data.py` — existing data tests; Phase 10 adds new `compute_campaign_agg` assertions for per-platform breakdown columns and `source_platforms`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `llm.py:CampaignAction` Pydantic model — add `source_platforms: list[str]` field alongside existing fields; no other model restructuring needed
- `llm.py:SYSTEM_PROMPT` Rules list — append two bullets (cross-platform comparison rule + source_platforms echo rule); list format already established
- `app.py` Run Analysis button pattern (lines 402–414) — the token gate UI wraps before this block; the existing `st.button("Run Analysis", type="primary")` stays as-is for the confirmed path
- `data.py:compute_campaign_agg()` — extend the `.agg()` call to include per-platform breakdowns; `groupby("campaign_id")` anchor stays the same

### Established Patterns
- `evidence_count` ← echoes `session_count` from input (llm.py:32–35 / SYSTEM_PROMPT line 5) — same pattern used for `source_platforms` ← echoes `source_platforms` column
- `st.status("...", expanded=True)` + `error_occurred` flag — established in app.py for the analysis flow; token gate sits BEFORE the `st.button` click, not inside the status block
- `_call_llm()` with `@retry` decorator — token preflight happens in `run_analysis()` before `_call_llm()` is invoked, keeping retry logic clean

### Integration Points
- `app.py` calls `run_analysis(st.session_state["campaign_agg"])` — `campaign_agg` now carries per-platform breakdown columns and `source_platforms`; `run_analysis` signature unchanged
- `compute_campaign_agg(merged_df)` output feeds directly into `run_analysis()` via `campaign_agg.to_csv()` — wider DataFrame with new columns goes into the CSV text verbatim
- Bridge block deletion: lines 362–371 in `app.py` are removed; `compute_campaign_agg` now handles source-prefixed columns natively so the bridge is no longer needed

</code_context>

<specifics>
## Specific Ideas

- `count_prompt_tokens(campaign_agg: pd.DataFrame) -> int` — new public helper in `llm.py` that `app.py` calls before showing the token gate. Uses `tiktoken.get_encoding("cl100k_base")`. Counts `len(SYSTEM_PROMPT tokens) + len(user_message tokens)` where user_message is the same f-string that `_call_llm()` would send. This keeps `run_analysis()` signature stable.
- Token gate in `app.py`: if `_token_count >= 60_000`: render `st.warning(...)` + a "Continue anyway" `st.button` with a session_state flag (`token_warning_confirmed`). Only after confirmation does the existing Run Analysis flow proceed.
- Per-platform breakdown column naming: `{platform_slug}_cost_usd` and `{platform_slug}_session_count` where `platform_slug` is extracted from source-prefixed column names already in `merged_df` (e.g., column `google_ads_cost_usd` → slug `google_ads` → display name `Google Ads` from `platform` column lookup).
- `source_platforms` in the agg CSV: pipe-delimited string `"Google Ads|Meta Ads"` — model splits on `|` in its head, but it's asked to echo the field verbatim into `list[str]`, so gpt-4o's structured output will parse it into the list correctly via the Pydantic schema.

</specifics>

<deferred>
## Deferred Ideas

- Interactive token breakdown UI (show which campaigns are largest) — Phase 11 charts scope
- Live tiktoken streaming estimate as user uploads files — v4+ (complexity not worth it for hackathon)
- Per-platform `semantic_reasoning` (separate reasoning strings per platform) — would require nested Pydantic schema; deferred until AGENT-01 value is proven in Phase 10

</deferred>

---

*Phase: 10-Richer-LLM-Analysis*
*Context gathered: 2026-06-02*
