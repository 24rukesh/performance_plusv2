---
phase: 12-analysis-persistence
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - app.py
  - data/fixture_results.json
  - llm.py
  - st_db.py
  - tests/test_evals.py
  - tests/test_llm.py
  - tests/test_st_db.py
findings:
  critical: 4
  warning: 3
  info: 2
  total: 9
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-06-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Phase 12 adds Postgres-backed analysis persistence (`st_db.py`), save/load/delete UI in `app.py`, observability logging in `llm.py`, and a new test suite (`test_evals.py`, `test_st_db.py`). The CRUD layer itself is well-structured and the mock-based unit tests are thorough. However, four blockers were found: the app crashes on startup when Postgres is unavailable, load-from-DB errors are not caught and will crash the sidebar, LLM-generated HTML is injected unescaped, and `run_analysis` will `AttributeError` at runtime if called with no API key and no `DEMO_MODE` flag. Three warnings cover missing Pydantic bounds on `percentage_change`, incomplete exception coverage in `app.py`'s save path, and an environment contamination risk in `test_evals.py`.

---

## Critical Issues

### CR-01: `init_db()` called at module level with no error guard — crashes app on every Streamlit startup when Postgres is absent

**File:** `app.py:21`

**Issue:** `st_db.init_db()` is called unconditionally at module level (outside any `try`/`except`) on every Streamlit rerun. `get_conn()` raises `RuntimeError("DATABASE_URL is not configured")` when the env var is absent, and `psycopg2.connect()` raises `psycopg2.OperationalError` when the DB is unreachable. Neither exception is caught at this call site. Both propagate to Streamlit's top-level handler, rendering a blank error page and preventing any use of the app — including demo-mode runs that need no DB at all.

The downstream `psycopg2.OperationalError` guards in the sidebar (line 143) and save button (line 537) are never reached because the app dies at line 21 first.

**Fix:**
```python
# app.py lines 19-21 — wrap init_db in a graceful degradation block
import st_db
import psycopg2

try:
    st_db.init_db()
except (RuntimeError, psycopg2.OperationalError) as _db_init_err:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Postgres unavailable at startup — persistence features disabled: %s", _db_init_err
    )
```

---

### CR-02: `load_analysis` `RuntimeError` and `pydantic.ValidationError` are not caught in the "Load" button path — crashes sidebar on row-not-found or schema drift

**File:** `app.py:134-142`

**Issue:** The `try` block covering the "Past Analyses" sidebar only catches `psycopg2.OperationalError` (line 143). Two additional exceptions can be raised inside the same block and are not caught:

1. `st_db.load_analysis(_row["id"])` (line 135) raises `RuntimeError(f"Analysis run {run_id} not found")` if the row was deleted between `list_analyses()` and the click (race condition, or concurrent session).
2. `AnalysisResult.model_validate(_p["analysis_result"])` (line 136) raises `pydantic.ValidationError` if the stored payload was saved under an older schema (schema drift between phases).

Both exceptions propagate out of the `with st.sidebar:` block, crashing the entire sidebar render and showing an unhandled exception traceback to the user.

**Fix:**
```python
    except (psycopg2.OperationalError, RuntimeError, Exception) as _load_err:
        st.sidebar.warning(
            "Could not load analysis — it may have been deleted or its schema has changed."
        )
```
Or more precisely, catch `psycopg2.OperationalError`, `RuntimeError`, and `pydantic.ValidationError` separately with targeted messages.

---

### CR-03: `run_analysis` crashes with `AttributeError: 'NoneType' object has no attribute 'beta'` when `client is None` and `DEMO_MODE` is not `"1"`

**File:** `llm.py:126-133`

**Issue:** The guard at line 126 only short-circuits to the fixture when **both** `DEMO_MODE == "1"` **and** `client is None`. When `DEMO_MODE` is unset (normal production deploy without an API key configured), `run_analysis` falls through to `_call_llm(csv_text)` at line 133, which immediately executes `client.beta.chat.completions.parse(...)` (line 101) — `AttributeError` on `None`.

The app-level UI guard (app.py line 402) normally prevents the Run Analysis button from appearing when `llm.client is None and not demo_ready`. However, `run_analysis` is a public function callable by other code paths (tests, future integrations), and the absence of an in-function guard means any direct call will crash. The `_call_llm` function itself also has no `client is None` guard.

**Fix:**
```python
def run_analysis(campaign_agg: pd.DataFrame) -> AnalysisResult:
    if os.environ.get("DEMO_MODE") == "1" and client is None:
        return _load_fixture()
    if client is None:
        raise ValueError(
            "OpenAI client is not initialised. Set OPENAI_API_KEY or enable DEMO_MODE=1."
        )
    # ... rest of function unchanged
```

---

### CR-04: LLM-generated strings injected into HTML without escaping — XSS risk

**File:** `ui_helpers.py:42,43,67`

**Issue:** Three LLM-generated string fields are interpolated directly into raw HTML fragments that are rendered via `unsafe_allow_html=True`:

- `build_exec_summary_html(summary)` (line 67): `executive_summary` from the LLM inserted as `{summary}` with no escaping.
- `build_results_table_html(result)` (line 42): `c.campaign_id` inserted as a raw table cell.
- `build_results_table_html(result)` (line 43): `c.semantic_reasoning` inserted as a raw table cell.

A maliciously crafted `campaign_id` (from a tampered input CSV) or a misbehaving LLM response containing `<script>` tags would execute JavaScript in the user's browser. Even with the current synthetic-data-only constraint, this is a stored-XSS pattern that must not be shipped as-is if real user data or multi-user tenancy is ever added.

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

**Issue:** The `CampaignAction.percentage_change` field is defined as a bare `int` with only a `description` hint. The `confidence` field (lines 39-42) correctly uses `ge=0.0, le=1.0`. The `percentage_change` field has no `ge` or `le` constraints, so a model response of `-500` or `+999` would pass Pydantic validation. This produces nonsensical display values (`+999%`) and could break downstream consumers that assume values in `[-100, +100]`.

**Fix:**
```python
percentage_change: int = Field(
    ge=-100,
    le=100,
    description="Signed integer -100 to +100. pause=-100, insufficient_data=0.",
)
```

No corresponding test covers this — `test_llm.py` tests `confidence` out-of-range rejection but not `percentage_change`. A `test_percentage_change_rejects_out_of_range` test should be added.

---

### WR-02: `save_analysis` catches only `psycopg2.OperationalError` — `RuntimeError` from `get_conn` (missing `DATABASE_URL`) surfaces as an unhandled exception on the save button

**File:** `app.py:537`

**Issue:** The `try/except` around the Save button (lines 529-538) only catches `psycopg2.OperationalError`. `st_db.get_conn()` raises `RuntimeError("DATABASE_URL is not configured")` when the env var is absent — a separate, non-subclassing exception type. This means clicking Save when `DATABASE_URL` is not set shows the user a raw Python traceback instead of the "Could not save" error message.

This is the mirror of CR-01 but localised to user interaction rather than startup. If CR-01 is fixed, the app survives startup and the user reaches the save button — where this catch gap then bites.

**Fix:**
```python
except (psycopg2.OperationalError, RuntimeError):
    st.error("Could not save — database unavailable.")
```

---

### WR-03: `test_evals.py` fallback tests are not guarded against `DEMO_MODE=1` in the environment — tests silently pass the wrong path and assert incorrectly

**File:** `tests/test_evals.py:56-75`

**Issue:** `test_openai_error_triggers_fallback` patches `llm._call_llm` with an OpenAI exception, then calls `run_analysis(...)`. If the test runs in an environment where `DEMO_MODE=1` **and** `llm.client is None` (the default when `OPENAI_API_KEY` is unset), `run_analysis` returns early at line 126 of `llm.py` — before `_call_llm` is ever called — and returns the fixture. The test then checks `mock_st.session_state.get("api_fallback_active") is True`, which fails because the early-return path never sets `api_fallback_active`. The same risk applies to `test_value_error_does_not_trigger_fallback`.

There is no `monkeypatch.delenv("DEMO_MODE", raising=False)` call in either test.

**Fix:**
```python
@pytest.mark.parametrize("exc_class", [...])
def test_openai_error_triggers_fallback(exc_class, monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)   # ADD THIS
    monkeypatch.setattr("llm.client", MagicMock())   # ADD THIS — ensure _call_llm is reached
    ...

def test_value_error_does_not_trigger_fallback(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)   # ADD THIS
    monkeypatch.setattr("llm.client", MagicMock())   # ADD THIS
    ...
```

---

## Info

### IN-01: `run_mode` values `'demo_mode'` and `'reload'` documented in `_log_analysis_run` docstring are dead — never passed by any caller

**File:** `st_db.py:166`

**Issue:** The `_log_analysis_run` docstring documents four valid `run_mode` values: `'live'`, `'fixture'`, `'demo_mode'`, `'reload'`. Only `'live'` and `'fixture'` are ever actually passed (from `llm.py:145`). The DEMO_MODE early-return path in `run_analysis` returns before reaching the logging call, and the DB-load path in `app.py` never calls `_log_analysis_run` at all. The docstring creates a false contract.

**Fix:** Update the docstring to remove the dead variants, or add logging calls in the demo-mode and load paths:
```python
    # run_mode: 'live' | 'fixture'
```

---

### IN-02: `filter_actions` multiselect omits `"INSUFFICIENT_DATA"` — campaigns with that action cannot be filtered by action type

**File:** `app.py:547`

**Issue:** The action type filter options are hardcoded as `["INCREASE", "DECREASE", "PAUSE"]`. The schema (`llm.py:32`) defines four valid actions including `"insufficient_data"`. When the LLM returns campaigns with `"insufficient_data"`, those campaigns cannot be selected or excluded via the filter. The color_discrete_map (line 510) correctly includes `"INSUFFICIENT_DATA"` for the bar chart, which highlights the inconsistency.

**Fix:**
```python
st.multiselect(
    "Action type",
    options=["INCREASE", "DECREASE", "PAUSE", "INSUFFICIENT_DATA"],
    key="filter_actions",
)
```

---

_Reviewed: 2026-06-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
