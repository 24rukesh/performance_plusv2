# Phase 12: Analysis Persistence - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Add analysis persistence to the Streamlit app: users can save the current analysis to Postgres with a label, reload any saved analysis from a sidebar list without re-uploading CSVs, and the app auto-falls back to a cached fixture response when the OpenAI API is unavailable.

**In scope:** New `st_db.py` module (psycopg2, `analysis_runs` table), Save button + label input in Campaign Actions tab, "Past Analyses" sidebar section (load + delete), DEMO_MODE auto-fallback in `llm.py` (try/except on the gpt-4o call).

**Out of scope:** Changes to `api/db.py` or the FastAPI service for this feature. Multi-user analysis isolation / auth. Analysis sharing or export of saved runs. Browsing/filtering saved analyses beyond the flat list.

</domain>

<decisions>
## Implementation Decisions

### DB Access Layer

- **D-01:** New `st_db.py` module in the repo root (alongside `app.py`), not inside `api/`. Connects to Postgres directly via psycopg2 reading `DATABASE_URL` env var — the same connection pattern as `api/db.py`. No HTTP calls to the FastAPI service.
- **D-02:** `st_db.py` has its own `init_db()` that runs `CREATE TABLE IF NOT EXISTS analysis_runs` on startup. Independent of `api/db.py`'s `init_db()`. Both are idempotent — running both is safe.
- **D-03:** `analysis_runs` table schema:
  ```sql
  CREATE TABLE IF NOT EXISTS analysis_runs (
      id        SERIAL PRIMARY KEY,
      label     TEXT NOT NULL,
      saved_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      payload   JSONB NOT NULL
  );
  ```
  Minimal schema — all rich data (analysis_result, campaign_agg, merged_df) lives in `payload` JSONB.

### Reloaded State Fidelity

- **D-04:** Full interactive state is restored on load. The `payload` JSONB stores all three session state pieces:
  - `analysis_result` — serialized via `AnalysisResult.model_dump()`
  - `campaign_agg` — serialized via `DataFrame.to_dict(orient="records")` (or `to_json()`)
  - `merged_df` — serialized via `DataFrame.to_dict(orient="records")` (or `to_json()`)
  After reload: Charts tab, Filters & Sort, session drill-down, comparison, and PDF/CSV export all work as if the analysis was just run.
- **D-05:** Loading a saved analysis replaces current session state silently — no confirmation prompt. `st.rerun()` is called after setting session state keys so the UI refreshes immediately.
- **D-06:** Each entry in the sidebar "Past Analyses" list has both a **Load** button and a small **✕ Delete** button. Delete removes the row from `analysis_runs` and calls `st.rerun()`.

### DEMO_MODE Auto-Fallback (MGMT-03)

- **D-07:** The gpt-4o call in `llm.py`'s `run_analysis()` is wrapped in `try/except openai.OpenAIError`. On any OpenAI exception, fall back to `_load_fixture()` and set `st.session_state["api_fallback_active"] = True`. This fires whether or not `DEMO_MODE=1` is set — it is a runtime auto-fallback, not a manual mode.
- **D-08:** When `api_fallback_active` is True, render `st.warning("OpenAI API unavailable — showing cached demo results")` at the top of the results section (above the tabs). Distinct from the existing `st.info` banner shown for the explicit `DEMO_MODE=1` env var.
- **D-09:** Catch `openai.OpenAIError` as the base class — covers `AuthenticationError`, `RateLimitError`, `APIConnectionError`, `APIStatusError`, and any future subclasses.

### Save/Load UI Placement

- **D-10:** The **Save Analysis** section lives at the top of the Campaign Actions tab (above the Filters & Sort expander), rendered only when `analysis_result is not None`. Layout: `st.text_input("Analysis label", ...)` next to a `st.button("💾 Save")`. On save, call `st_db.save_analysis(label, payload)` and show `st.success("Saved.")`.
- **D-11:** The **Past Analyses** list lives in the sidebar as a section (e.g., `st.sidebar.subheader("Past Analyses")` or `st.sidebar.expander`). Each entry renders: `label — saved_at date` with a **Load** button and a **✕** button beside it. List is fetched fresh on each rerun via `st_db.list_analyses()`.
- **D-12:** No auto-navigation after loading — `st.rerun()` fires and the user lands on whatever tab was active. No session state tab-index tracking required.

### Session State Additions

- **D-13:** Add `"api_fallback_active": False` to the `_state_defaults` initialization block in `app.py` (alongside existing keys). Reset to `False` when a new live analysis starts.

### Claude's Discretion

- DataFrame serialization format inside JSONB payload — `to_dict(orient="records")` vs `to_json()` — Claude picks whichever round-trips cleanly through `pd.DataFrame(json_data)` on load.
- Exact sidebar layout for the "Past Analyses" section — `st.expander` or inline `st.sidebar.markdown` — Claude picks what renders cleanly.
- Whether `st_db.init_db()` is called at module import or explicitly called once in `app.py` startup — Claude decides based on Streamlit re-run behavior.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Primary source files (read before touching)
- `app.py` — full file — session state init block (lines ~127–145), results section (`if analysis_result is not None:` block ~line 413+), DEMO_MODE flag (line 49), existing sidebar structure
- `llm.py` — `run_analysis()` function (lines ~118–130), `_load_fixture()` (lines ~134–138), `AnalysisResult`/`CampaignAction` Pydantic models — D-07 modifies `run_analysis()` with try/except
- `api/db.py` — psycopg2 connection pattern (`get_conn()`, `init_db()`) — `st_db.py` follows the same structure

### Requirements
- `.planning/REQUIREMENTS.md` — MGMT-01 (save/load to Postgres), MGMT-03 (DEMO_MODE fallback) — the two requirements this phase delivers
- `.planning/ROADMAP.md` — Phase 12 success criteria (3 items) — verify all 3 are satisfied

### Prior phase context
- `.planning/phases/11-charts-filters-export/11-CONTEXT.md` — D-01 (3-tab layout: Data Preview / Charts / Campaign Actions), D-10/D-11 (export buttons at bottom of Campaign Actions tab) — Phase 12 inserts Save section at the TOP of Campaign Actions tab, above filters
- `.planning/phases/10-richer-llm-analysis/10-CONTEXT.md` — D-07 (source_platforms field), session state keys added in Phase 10

### Existing patterns
- `api/db.py` — canonical psycopg2 pattern for this project (get_conn, init_db, CRUD functions); `st_db.py` must follow the same structure

### Test regression net
- `tests/` — run full test suite after Phase 12; no existing tests for db or llm fallback path — Phase 12 should add tests for `st_db.py` CRUD and `llm.py` fallback

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/db.py` — `get_conn()` / `init_db()` pattern — copy structure directly into `st_db.py`; use `psycopg2.extras.Json` for JSONB serialization (already imported in `api/db.py`)
- `llm._load_fixture()` — already loads `data/fixture_results.json` and validates via `AnalysisResult.model_validate()`; Phase 12 calls this from the except branch in `run_analysis()`
- `st.session_state["analysis_result"]` / `["campaign_agg"]` / `["merged_df"]` — the three objects to serialize into `payload` JSONB on save, and restore on load

### Established Patterns
- `_state_defaults` dict initialization (app.py lines ~127–145) — Phase 12 adds `"api_fallback_active": False` here
- `st.session_state` key guard (`if k not in st.session_state`) — follow same pattern for any new keys
- `DEMO_MODE` + `demo_mode_active` flags — the existing explicit DEMO_MODE path is NOT changed; D-07 adds a second, independent fallback that activates at runtime

### Integration Points
- Campaign Actions tab (`st.tabs` result, index 2) — Phase 12 inserts Save section at the very top, before the Filters & Sort expander (D-10)
- Sidebar — Phase 12 adds "Past Analyses" section below existing sidebar content (D-11)
- `llm.py run_analysis()` — wrap the `client.beta.chat.completions.parse(...)` call with try/except (D-07)
- `app.py` startup — call `st_db.init_db()` once at app startup (after DEMO_MODE flag resolution, before UI rendering)

</code_context>

<specifics>
## Specific Ideas

- `st_db.save_analysis(label: str, payload: dict) -> int` — inserts row, returns new `id`
- `st_db.list_analyses() -> list[dict]` — returns rows as `[{"id": ..., "label": ..., "saved_at": ...}, ...]` ordered by `saved_at DESC`; used to render sidebar list
- `st_db.load_analysis(run_id: int) -> dict` — returns `payload` JSONB for the given `id`
- `st_db.delete_analysis(run_id: int) -> None` — deletes row by `id`
- On load: `result = AnalysisResult.model_validate(payload["analysis_result"])`, `campaign_agg = pd.DataFrame(payload["campaign_agg"])`, `merged_df = pd.DataFrame(payload["merged_df"])`, then set session state keys and call `st.rerun()`
- Sidebar entry display: `f"{row['label']} — {row['saved_at'].strftime('%b %d, %H:%M')}"` with Load + ✕ buttons in `st.columns([3, 1, 1])`

</specifics>

<deferred>
## Deferred Ideas

- Analysis sharing / permalink — would require auth and multi-user isolation; v4+
- Browsing/filtering saved analyses by date or platform — flat list is sufficient for Phase 12; v4+
- Comparing two saved analyses side-by-side — v4+
- Auto-save after every analysis run — could overload the list; require explicit user save for now

</deferred>

---

*Phase: 12-Analysis-Persistence*
*Context gathered: 2026-06-04*
