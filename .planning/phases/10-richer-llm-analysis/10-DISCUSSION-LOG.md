# Phase 10: Richer LLM Analysis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 10-richer-llm-analysis
**Areas discussed:** Agg shape for LLM, Token preflight UX, Cross-platform prompt, Extra CRM cols in prompt

---

## Agg shape for LLM

### Q1: How should per-platform data reach gpt-4o?

| Option | Description | Selected |
|--------|-------------|----------|
| Breakdown columns | One row per campaign, per-platform columns alongside unified totals | ✓ |
| Platform rows | Pivot to one row per campaign+platform | |
| Totals only + prompt hint | Keep unified totals; add source_platforms column only | |

**User's choice:** Breakdown columns
**Notes:** Richer LLM context without changing row count; consistent with how evidence_count echoes session_count.

### Q2: Which per-platform metrics as breakdown columns?

| Option | Description | Selected |
|--------|-------------|----------|
| Cost + sessions | Per-platform: cost_usd and session_count only | ✓ |
| Cost + sessions + clicks | Per-platform: cost_usd, session_count, clicks | |
| Full breakdown | Per-platform: cost_usd, session_count, clicks, impressions, conversion_rate | |

**User's choice:** Cost + sessions only
**Notes:** Lean enough to keep CSV tokens manageable; sufficient for "lead quality per dollar" reasoning.

### Q3: source_platforms population strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Python pre-computes, model echoes | source_platforms column in CSV; model echoes it | ✓ |
| Model infers freely | No column; model infers from breakdown columns | |

**User's choice:** Python pre-computes, model echoes
**Notes:** Deterministic; same echo pattern as evidence_count ↔ session_count.

---

## Token preflight UX

### Q1: Behavior when 60k token threshold is approached

| Option | Description | Selected |
|--------|-------------|----------|
| Warning + gate | st.warning + "Continue anyway" button required | ✓ |
| Non-blocking warning | st.warning shown but Run Analysis proceeds normally | |
| Hard block | st.error + st.stop() above threshold | |

**User's choice:** Warning + gate
**Notes:** Prevents accidental expensive/truncated calls during live demo.

### Q2: Token threshold and warning message

| Option | Description | Selected |
|--------|-------------|----------|
| 60k with count shown | Threshold: 60,000; message shows exact count | ✓ |
| 75% of 128k (~96k) | Threshold: 96,000 | |
| 50k conservative | Threshold: 50,000 | |

**User's choice:** 60k with count shown
**Notes:** Matches AGENT-03 specification exactly.

---

## Cross-platform prompt

### Q1: How to update SYSTEM_PROMPT for cross-platform comparison

| Option | Description | Selected |
|--------|-------------|----------|
| Add bullet to SYSTEM_PROMPT | One new rule in existing Rules list | ✓ |
| Dedicated comparison section | New ## section with 2-3 bullets | |
| User message restructure | Platform Summary table in user message, SYSTEM_PROMPT unchanged | |

**User's choice:** Add bullet to SYSTEM_PROMPT
**Notes:** Minimal change; keeps existing structure.

### Q2: Update executive_summary field description

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — update description | Add "which platform delivers best lead quality" to field description | ✓ |
| No — leave as-is | Cross-platform appears in semantic_reasoning only | |

**User's choice:** Yes — update description
**Notes:** Ensures summary-level output reflects multi-source analysis.

---

## Extra CRM cols in prompt

### Q1: Should crm_-prefixed pass-through columns reach gpt-4o?

| Option | Description | Selected |
|--------|-------------|----------|
| Concatenate into sales_notes | Append as "field: value" to sales_notes aggregation string | ✓ |
| Separate agg columns | New columns in CSV per crm_ field | |
| Exclude — defer to Phase 11 | Keep prompt lean; surface in results view later | |

**User's choice:** Concatenate into sales_notes
**Notes:** Zero schema change; LLM sees extra context as part of qualitative signal.

---

## Claude's Discretion

- Whether `run_analysis` returns a tuple `(AnalysisResult, int)` or delegates token counting to a separate `count_prompt_tokens()` helper — preferred: separate helper to keep `run_analysis()` signature stable.
- Source-prefix column detection pattern (regex vs. endswith) — endswith is simpler and sufficient.
- Platform slug extraction from source-prefixed column names vs. `platform` string column — use column names to avoid slug/display-name mismatch.

## Deferred Ideas

- Interactive token breakdown UI (show which campaigns are the largest token contributors) — Phase 11 charts scope.
- Live tiktoken streaming estimate as user uploads files — v4+.
- Per-platform `semantic_reasoning` (separate reasoning strings per platform) — requires nested Pydantic schema; defer until AGENT-01 value is proven.
