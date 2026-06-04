# Phase 12: Analysis Persistence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 12-Analysis-Persistence
**Areas discussed:** DB access from Streamlit, Reloaded state fidelity, DEMO_MODE auto-fallback, Save/load UI placement

---

## DB Access from Streamlit

| Option | Description | Selected |
|--------|-------------|----------|
| Direct psycopg2 (st_db.py) | New module in repo root, reads DATABASE_URL, same pattern as api/db.py | ✓ |
| HTTP to FastAPI | app.py calls POST/GET /api/analyses endpoints via requests | |
| Inline in app.py | psycopg2 imports and DB calls directly inside app.py | |

**User's choice:** Direct psycopg2 — new `st_db.py` module

---

| Option | Description | Selected |
|--------|-------------|----------|
| st_db.py creates its own table on startup | Independent init_db() with CREATE TABLE IF NOT EXISTS analysis_runs | ✓ |
| Extend api/db.py with analysis_runs | FastAPI service manages all table creation, st_db.py only reads/writes | |

**User's choice:** st_db.py creates its own table — independent, idempotent

---

| Option | Description | Selected |
|--------|-------------|----------|
| id, label, saved_at, payload JSONB | Minimal schema — all rich data in JSONB | ✓ |
| Add run_metadata columns | id, label, saved_at, platform_count, session_count, reporting_currency, payload JSONB | |

**User's choice:** Minimal schema — `id, label, saved_at, payload JSONB`

---

## Reloaded State Fidelity

| Option | Description | Selected |
|--------|-------------|----------|
| Full interactive state | Restore analysis_result + campaign_agg + merged_df — all three in JSONB | ✓ |
| AI results only | Restore only analysis_result; Charts tab shows placeholder | |

**User's choice:** Full interactive state — Charts tab, filters, drill-down all work after reload

---

| Option | Description | Selected |
|--------|-------------|----------|
| Replace silently | Overwrite session state directly, no confirmation prompt | ✓ |
| Warn if unsaved changes | Show st.warning before overwriting if current analysis unsaved | |

**User's choice:** Replace silently

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, small delete button per entry | Load + ✕ delete buttons for each saved analysis | ✓ |
| No delete in Phase 12 | Load only, deletion is v4+ | |

**User's choice:** Yes — delete button per entry

---

## DEMO_MODE Auto-Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-catch at runtime | try/except openai.OpenAIError in run_analysis(), fall back to fixture | ✓ |
| Keep explicit DEMO_MODE=1 only | Don't change runtime call path; existing env var is the 'unavailable' mode | |

**User's choice:** Auto-catch at runtime — MGMT-03 means genuine runtime fallback, not just manual mode

---

| Option | Description | Selected |
|--------|-------------|----------|
| st.warning banner in results | st.warning at top of results section when fallback fires | ✓ |
| Inline caption only | Small st.caption below results header | |

**User's choice:** st.warning banner — clear, non-blocking

---

| Option | Description | Selected |
|--------|-------------|----------|
| All openai.OpenAIError subclasses | Catch base class — covers all error types | ✓ |
| Specific exceptions only | AuthenticationError + APIConnectionError only; let rate limits propagate | |

**User's choice:** All openai.OpenAIError subclasses

---

## Save/Load UI Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Inside results area | Save button + label input at top of Campaign Actions tab | ✓ |
| Sidebar only | Save button in sidebar above the saved analyses list | |

**User's choice:** Inside results area — co-located with the results it saves

---

| Option | Description | Selected |
|--------|-------------|----------|
| Sidebar section | "Past Analyses" section at bottom of sidebar, load + delete per entry | ✓ |
| Dedicated 'History' tab | 4th tab alongside Data Preview / Charts / Campaign Actions | |

**User's choice:** Sidebar section — always accessible regardless of active tab

---

| Option | Description | Selected |
|--------|-------------|----------|
| No auto-navigation | st.rerun() fires, user stays on current tab | ✓ |
| Auto-navigate to Campaign Actions | Force active tab to Campaign Actions after loading | |

**User's choice:** No auto-navigation — simpler, no tab-index tracking required

---

## Claude's Discretion

- DataFrame serialization format inside JSONB payload — `to_dict(orient="records")` vs `to_json()`
- Sidebar layout for "Past Analyses" section — `st.expander` vs inline `st.sidebar.markdown`
- Whether `st_db.init_db()` is called at module import or explicitly in app.py startup

## Deferred Ideas

- Analysis sharing / permalink — v4+ (requires auth + multi-user isolation)
- Browse/filter saved analyses by date or platform — v4+
- Comparing two saved analyses side-by-side — v4+
- Auto-save after every analysis run — explicit user save only for now
