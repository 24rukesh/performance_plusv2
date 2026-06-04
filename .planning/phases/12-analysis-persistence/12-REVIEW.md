---
phase: 12-analysis-persistence
reviewed: 2026-06-04T12:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - app.py
  - tests/test_evals.py
findings:
  critical: 2
  warning: 1
  info: 2
  total: 5
status: issues_found
---

# Phase 12: Code Review Report (Updated — post gap-closure plan 12-05)

**Reviewed:** 2026-06-04T12:00:00Z
**Depth:** standard
**Files Reviewed:** 2 (app.py, tests/test_evals.py)
**Status:** issues_found

## Summary

This update covers the gap-closure changes from plan 12-05, which targeted CR-01, WR-02, and WR-03 from the prior review. All three targeted fixes are confirmed present and correct:

- **CR-01 closed:** `st_db.init_db()` at app.py lines 21-25 is now wrapped in `try/except (RuntimeError, psycopg2.OperationalError)` with a `logging.warning` fallback — app starts cleanly without Postgres.
- **WR-02 closed:** The save button's except clause at app.py line 541 now correctly catches `(psycopg2.OperationalError, RuntimeError)` — users see a friendly error instead of a raw traceback when `DATABASE_URL` is absent.
- **WR-03 closed:** Both fallback tests in `test_evals.py` now include `monkeypatch.delenv("DEMO_MODE", raising=False)` and `monkeypatch.setattr("llm.client", MagicMock())` — the tests are deterministic regardless of ambient `DEMO_MODE` state.

Two critical issues from the original review remain open (CR-02 and CR-04) because they were explicitly descoped from plan 12-05. They are reprinted below with no change in severity. WR-01 (Pydantic bounds on `percentage_change`) also remains open. Two info items are retained.

---

## Critical Issues

### CR-02: `load_analysis` `RuntimeError` and `pydantic.ValidationError` not caught in the "Load" button path — crashes sidebar on row-not-found or schema drift

**File:** `app.py:138-147`

**Issue:** The `try` block covering the "Past Analyses" sidebar catches only `psycopg2.OperationalError` (line 147). Two additional exceptions can fire inside the same block and are not caught:

1. `st_db.load_analysis(_row["id"])` (line 139) raises `RuntimeError(f"Analysis run {run_id} not found")` when a row is deleted between `list_analyses()` and the button click — a race condition in any multi-tab or multi-user session.
2. `AnalysisResult.model_validate(_p["analysis_result"])` (line 140) raises `pydantic.ValidationError` if the stored payload was saved under an earlier schema version (schema drift between phases).

Both exceptions propagate outside the `with st.sidebar:` block, crashing the entire sidebar render and showing an unhandled exception traceback to the user. The `delete_analysis` call at line 145 (also inside the same `try`) can similarly raise `RuntimeError` if `DATABASE_URL` is absent — caught by `psycopg2.OperationalError` only when the DB is reachable but not when the env var itself is missing.

**Fix:**
```python
    except (psycopg2.OperationalError, RuntimeError) as _side_err:
        st.sidebar.warning(
            "Could not load/delete analysis — it may have been removed or its schema has changed."
        )
```
For maximum precision, catch `pydantic.ValidationError` explicitly with a targeted message (import `from pydantic import ValidationError`):
```python
    except psycopg2.OperationalError:
        st.sidebar.warning("Postgres unavailable — saved analyses cannot be shown.")
    except RuntimeError:
        st.sidebar.warning("Could not complete operation — database not configured.")
    except ValidationError:
        st.sidebar.warning("Saved analysis format has changed — please delete and re-save.")
```

---

### CR-04: LLM-generated strings injected into HTML without escaping — XSS risk

**File:** `ui_helpers.py:39,42,67`

**Issue:** Three string fields sourced from LLM output (or user-supplied CSV content) are interpolated directly into raw HTML rendered via `unsafe_allow_html=True` in `app.py`:

- `build_exec_summary_html(summary)` (line 67): `executive_summary` from the LLM is embedded as `{summary}` with no escaping.
- `build_results_table_html(result)` (line 39): `c.campaign_id` — derived from user-uploaded CSV — embedded raw into a `<td>`.
- `build_results_table_html(result)` (line 42): `c.semantic_reasoning` from the LLM embedded raw into a `<td>`.

A `campaign_id` in a tampered CSV containing `<script>alert(1)</script>` — or a misbehaving LLM completion — would execute JavaScript in the user's browser. The current synthetic-data-only constraint limits immediate exposure, but this is a stored-XSS pattern that will become exploitable if real user data or multi-tenant access is ever added (both are on the v2 roadmap per `CLAUDE.md`).

**Fix:**
```python
# Add at top of ui_helpers.py
from html import escape

# In build_exec_summary_html:
f"<strong>This week:</strong> {escape(summary)}"

# In build_results_table_html rows loop:
f"<td style='padding:8px 12px;'>{escape(c.campaign_id)}</td>"
f"<td style='padding:8px 12px;'>{escape(c.semantic_reasoning)}</td>"
```

---

## Warnings

### WR-01: `percentage_change` field has no Pydantic bounds constraints — LLM can return values outside `[-100, +100]`

**File:** `llm.py:33-35`

**Issue:** `CampaignAction.percentage_change` is defined as a bare `int` with only a description hint. The `confidence` field (lines 39-42) correctly uses `ge=0.0, le=1.0` validators. Without `ge`/`le` constraints on `percentage_change`, a model response of `-500` or `+999` passes validation silently, producing nonsensical UI labels (`+999%`) and potentially breaking downstream consumers that assume the `[-100, +100]` range stated in the docstring.

**Fix:**
```python
percentage_change: int = Field(
    ge=-100,
    le=100,
    description="Signed integer -100 to +100. pause=-100, insufficient_data=0.",
)
```
A corresponding test (`test_percentage_change_rejects_out_of_range`) should also be added to `tests/test_llm.py` — `confidence` out-of-range is tested but `percentage_change` is not.

---

## Info

### IN-01: `run_mode` values `'demo_mode'` and `'reload'` in `_log_analysis_run` docstring are dead — never passed by any caller

**File:** `st_db.py` (not in this review's file scope; retained from prior review for tracking)

**Issue:** The `_log_analysis_run` docstring documents four valid `run_mode` values: `'live'`, `'fixture'`, `'demo_mode'`, `'reload'`. Only `'live'` and `'fixture'` are ever actually passed (from `llm.py:145`). The DEMO_MODE early-return path in `run_analysis` returns before reaching the logging call, and the DB-load path in `app.py` never calls `_log_analysis_run`. The docstring creates a false contract.

**Fix:** Update the docstring to remove the dead variants:
```python
    # run_mode: 'live' | 'fixture'
```

---

### IN-02: `filter_actions` multiselect omits `"INSUFFICIENT_DATA"` — campaigns with that action cannot be filtered by action type

**File:** `app.py:551`

**Issue:** The action type filter options are hardcoded as `["INCREASE", "DECREASE", "PAUSE"]`. The schema (`llm.py:32`) defines four valid actions including `"insufficient_data"`. When the LLM returns campaigns with `"insufficient_data"`, those campaigns cannot be selected or excluded via the filter. The `color_discrete_map` at app.py line 510 correctly handles `"INSUFFICIENT_DATA"` in the bar chart, highlighting the inconsistency.

**Fix:**
```python
st.multiselect(
    "Action type",
    options=["INCREASE", "DECREASE", "PAUSE", "INSUFFICIENT_DATA"],
    key="filter_actions",
)
```

---

## Gap-Closure Verification Summary

| Finding | Prior Status | Plan 12-05 Fix | Current Status |
|---------|-------------|----------------|----------------|
| CR-01 — `init_db()` unguarded at startup | OPEN (BLOCKER) | Wrapped in `try/except (RuntimeError, psycopg2.OperationalError)` at app.py lines 21-25 | **CLOSED** |
| CR-02 — Load button missing `RuntimeError`/`ValidationError` catch | OPEN | Not in scope for plan 12-05 | **OPEN** |
| CR-03 — `run_analysis` AttributeError when `client is None` and no `DEMO_MODE` | OPEN | Not in scope for plan 12-05 | OPEN (pre-existing; not reprinted — UI gate in app.py prevents reaching this in the running app; only affects direct callers) |
| CR-04 — XSS via unescaped LLM output in `ui_helpers.py` | OPEN | Not in scope for plan 12-05 | **OPEN** |
| WR-01 — `percentage_change` missing Pydantic bounds | OPEN | Not in scope for plan 12-05 | **OPEN** |
| WR-02 — Save button catches only `OperationalError`, not `RuntimeError` | OPEN (WARNING) | Expanded to `(psycopg2.OperationalError, RuntimeError)` at app.py line 541 | **CLOSED** |
| WR-03 — `test_evals.py` fallback tests environmentally fragile | OPEN (WARNING) | `monkeypatch.delenv` + `monkeypatch.setattr("llm.client", ...)` added to both tests | **CLOSED** |

---

_Reviewed: 2026-06-04T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
