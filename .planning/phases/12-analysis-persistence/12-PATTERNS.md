# Phase 12: Analysis Persistence - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 3 (1 new, 2 modified)
**Analogs found:** 3 / 3

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `st_db.py` (NEW) | data-layer / persistence module | CRUD | `api/db.py` | exact |
| `app.py` (MODIFY) | UI layer / Streamlit shell | request-response | `app.py` itself (read current state) | self |
| `llm.py` (MODIFY) | business logic / LLM orchestration | request-response | `llm.py` itself (read current state) | self |

---

## Pattern Assignments

### `st_db.py` (NEW — data layer, CRUD)

**Analog:** `api/db.py`

**Imports pattern** (`api/db.py` lines 1–7):
```python
import os

import psycopg2
import psycopg2.errors
import psycopg2.extras  # required: Json adapter + JSONB auto-deserialization
from psycopg2.extras import Json
```
Note: drop the `from fastapi import HTTPException` import — `st_db.py` is not a FastAPI module. Replace with plain Python exceptions where needed.

**Connection pattern** (`api/db.py` lines 10–15):
```python
def get_conn():
    """Open a new connection. Caller is responsible for close()."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(url)
```
Copy verbatim — identical env var name and contract.

**init_db pattern** (`api/db.py` lines 18–53):
```python
def init_db() -> None:
    """Create tables if they don't exist. Called at lifespan startup."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_runs (
                        id        SERIAL PRIMARY KEY,
                        label     TEXT NOT NULL,
                        saved_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        payload   JSONB NOT NULL
                    )
                """)
    finally:
        conn.close()
```
Use the `with conn: / with conn.cursor() as cur:` double-context-manager structure exactly as in `api/db.py`. The `with conn:` block auto-commits on success and rolls back on exception — do not add manual `conn.commit()`.

**INSERT with JSONB pattern** (`api/db.py` lines 56–71):
```python
def insert_analysis_result(campaign_id: str, run_id: str, result) -> None:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analysis_results
                        (campaign_id, run_id, analyzed_at, result_json)
                    VALUES (%s, %s::uuid, NOW(), %s)
                    """,
                    (campaign_id, run_id, Json(result.model_dump())),
                )
    finally:
        conn.close()
```
For `st_db.save_analysis()`, follow the same shape but return the new `id` via `RETURNING id` + `cur.fetchone()[0]`. Use `Json(payload)` for the JSONB column. Signature: `save_analysis(label: str, payload: dict) -> int`.

**SELECT pattern** (`api/db.py` lines 74–92):
```python
def get_latest_result(campaign_id: str) -> dict | None:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT result_json FROM analysis_results
                    WHERE campaign_id = %s
                    ORDER BY analyzed_at DESC
                    LIMIT 1
                    """,
                    (campaign_id,),
                )
                row = cur.fetchone()
                return row[0] if row else None
    finally:
        conn.close()
```
For `st_db.list_analyses()`, use `cur.fetchall()` and map rows to `[{"id": row[0], "label": row[1], "saved_at": row[2]}]`. For `st_db.load_analysis(run_id)`, select `payload` WHERE `id = %s` and return `row[0]` (psycopg2 auto-deserializes JSONB to dict when `psycopg2.extras` is imported).

**DELETE pattern** (derive from insert pattern above):
```python
def delete_analysis(run_id: int) -> None:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM analysis_runs WHERE id = %s", (run_id,))
    finally:
        conn.close()
```

**Full function signatures for `st_db.py`:**
```python
def get_conn() -> psycopg2.connection: ...
def init_db() -> None: ...
def save_analysis(label: str, payload: dict) -> int: ...
def list_analyses() -> list[dict]: ...      # [{"id", "label", "saved_at"}, ...]
def load_analysis(run_id: int) -> dict: ... # returns payload JSONB as dict
def delete_analysis(run_id: int) -> None: ...
```

---

### `app.py` (MODIFY — UI layer, request-response)

**Analog:** `app.py` (current file — all modifications integrate with existing patterns)

**Session state initialization pattern** (`app.py` lines 127–145):
```python
_state_defaults = {
    "merged_df": None,
    "campaign_agg": None,
    "analysis_result": None,
    # Phase 9 additions:
    "google_ads_bytes": None,
    ...
    "demo_mode_active": False,
    # Phase 10 addition:
    "token_warning_confirmed": False,
}
for k, v in _state_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
```
Add `"api_fallback_active": False` to `_state_defaults` following the same comment convention (`# Phase 12 addition:`). The guard pattern `if k not in st.session_state` is already correct — do not change it.

**`st.rerun()` pattern** (`app.py` lines 387–388, 529–530):
```python
if st.button("Continue anyway", key="token_confirm_btn"):
    st.session_state["token_warning_confirmed"] = True
    st.rerun()
```
and
```python
if st.button("Reset filters", key="reset_filters_btn"):
    for k in ["filter_platforms", "filter_actions", "filter_name"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()
```
On Load and Delete in the sidebar: set session state keys then call `st.rerun()` immediately — same pattern.

**st.status / error handling pattern** (`app.py` lines 394–408):
```python
with st.status("Analysing campaigns...", expanded=True) as status:
    status.write("Loading demo analysis..." if demo_ready else "Calling gpt-4o...")
    try:
        result = llm._load_fixture() if demo_ready else run_analysis(st.session_state["campaign_agg"])
    except Exception:
        status.update(label="Analysis failed", state="error")
        error_occurred = True
    if not error_occurred:
        status.write("Structuring output...")
        st.session_state["analysis_result"] = result
        status.update(label="Done ✓", state="complete", expanded=False)
if error_occurred:
    st.error("Analysis failed. Check your OPENAI_API_KEY or retry.")
    st.stop()
```
After D-07 lands in `llm.py`, the `except Exception` here will never see an `OpenAIError` (it falls back inside `run_analysis()`). This block stays unchanged. A separate `st.warning(...)` for `api_fallback_active` renders at the **top of the results section** (above `st.tabs`), not inside `st.status`.

**api_fallback_active warning placement** — insert immediately before `st.tabs(...)` at line 431:
```python
if st.session_state["analysis_result"] is not None:
    result = st.session_state["analysis_result"]

    # Phase 12 D-08: runtime API fallback banner
    if st.session_state.get("api_fallback_active"):
        st.warning("OpenAI API unavailable — showing cached demo results")

    # ... existing qual_counts / chart_df setup ...

    tab_preview, tab_charts, tab_actions = st.tabs(["Data Preview", "Charts", "Campaign Actions"])
```

**Save Analysis UI placement** — top of `tab_actions` block (line 483), before the `with st.expander("Filters & Sort"...)`:
```python
with tab_actions:
    # Phase 12 D-10: Save Analysis — top of tab, before Filters & Sort
    if st.session_state["analysis_result"] is not None:
        _save_col, _btn_col = st.columns([4, 1])
        with _save_col:
            _save_label = st.text_input("Analysis label", key="save_label_input",
                                        placeholder="e.g. Q2 2026 Campaign Review")
        with _btn_col:
            st.write("")  # vertical alignment spacer
            if st.button("💾 Save", key="save_analysis_btn"):
                _payload = {
                    "analysis_result": st.session_state["analysis_result"].model_dump(),
                    "campaign_agg": st.session_state["campaign_agg"].to_dict(orient="records"),
                    "merged_df": st.session_state["merged_df"].to_dict(orient="records"),
                }
                st_db.save_analysis(_save_label or "Untitled", _payload)
                st.success("Saved.")

    # existing: Filters & Sort expander
    with st.expander("🔍 Filters & Sort", expanded=False):
        ...
```

**Sidebar section pattern** — append after existing sidebar blocks (after "Demo Data" section):
```python
with st.sidebar:
    # ... existing: API key, Reporting Currency, Demo Data ...

    # Phase 12 D-11: Past Analyses section
    st.subheader("Past Analyses")
    _past = st_db.list_analyses()
    if not _past:
        st.caption("No saved analyses yet.")
    for _row in _past:
        _entry_label = f"{_row['label']} — {_row['saved_at'].strftime('%b %d, %H:%M')}"
        _c1, _c2, _c3 = st.columns([3, 1, 1])
        _c1.markdown(_entry_label)
        if _c2.button("Load", key=f"load_run_{_row['id']}"):
            _payload = st_db.load_analysis(_row["id"])
            st.session_state["analysis_result"] = AnalysisResult.model_validate(_payload["analysis_result"])
            st.session_state["campaign_agg"] = pd.DataFrame(_payload["campaign_agg"])
            st.session_state["merged_df"] = pd.DataFrame(_payload["merged_df"])
            st.rerun()
        if _c3.button("✕", key=f"del_run_{_row['id']}"):
            st_db.delete_analysis(_row["id"])
            st.rerun()
```

**init_db call placement** — at app startup, after `load_dotenv()` and before the sidebar block (around line 17):
```python
load_dotenv()

import st_db  # Phase 12: Streamlit-side DB module
st_db.init_db()  # idempotent — safe to call on every rerun
```

**Reset `api_fallback_active` on new analysis** — inside the Run Analysis button handler (around line 393), before calling `run_analysis()`:
```python
if st.button("Run Analysis", type="primary"):
    st.session_state["api_fallback_active"] = False  # Phase 12: reset before each run
    error_occurred = False
    with st.status(...) as status:
        ...
```

---

### `llm.py` (MODIFY — business logic, request-response)

**Analog:** `llm.py` (current file — wraps existing `_call_llm()` call in `run_analysis()`)

**Current `run_analysis()` body** (`llm.py` lines 118–131):
```python
def run_analysis(campaign_agg: pd.DataFrame) -> AnalysisResult:
    """Serialize campaign_agg as CSV and send to gpt-4o. Returns a validated AnalysisResult."""
    # per D-01, D-11: fixture path when DEMO_MODE=1 and no live key is present
    if os.environ.get("DEMO_MODE") == "1" and client is None:
        return _load_fixture()
    t0 = time.perf_counter()
    csv_text = campaign_agg.to_csv(index=False)
    result = _call_llm(csv_text)
    logger.info(
        "run_analysis completed in %.2fs | campaigns=%d",
        time.perf_counter() - t0,
        len(result.campaigns),
    )
    return result
```

**Modified `run_analysis()` with try/except fallback** (D-07, D-08, D-09):
```python
import openai  # add to existing imports at top of file

def run_analysis(campaign_agg: pd.DataFrame) -> AnalysisResult:
    """Serialize campaign_agg as CSV and send to gpt-4o. Returns a validated AnalysisResult.

    On any OpenAI API error, falls back to fixture and sets
    st.session_state["api_fallback_active"] = True (D-07).
    """
    if os.environ.get("DEMO_MODE") == "1" and client is None:
        return _load_fixture()
    t0 = time.perf_counter()
    csv_text = campaign_agg.to_csv(index=False)
    try:
        result = _call_llm(csv_text)
    except openai.OpenAIError as exc:
        logger.warning("OpenAI API error — falling back to fixture: %s", exc)
        try:
            import streamlit as st
            st.session_state["api_fallback_active"] = True
        except Exception:
            pass  # non-Streamlit callers (tests) — silently skip
        return _load_fixture()
    logger.info(
        "run_analysis completed in %.2fs | campaigns=%d",
        time.perf_counter() - t0,
        len(result.campaigns),
    )
    return result
```

**`openai.OpenAIError` base class coverage** — this single base catches all subclasses per D-09:
- `openai.AuthenticationError`
- `openai.RateLimitError`
- `openai.APIConnectionError`
- `openai.APIStatusError`

**`_load_fixture()` — no changes needed** (`llm.py` lines 134–138):
```python
def _load_fixture() -> AnalysisResult:
    # per D-02: fixture lives at data/fixture_results.json, loaded via model_validate
    fixture_path = Path(__file__).parent / "data" / "fixture_results.json"
    data = json.loads(fixture_path.read_text())
    return AnalysisResult.model_validate(data)
```
Called from both the existing DEMO_MODE path and the new except branch — no modification required.

**tenacity interaction** — `_call_llm()` is decorated with `@retry` (`llm.py` lines 93–97). The `@retry` decorator exhausts 3 attempts before raising. The `try/except openai.OpenAIError` in `run_analysis()` wraps the already-retried `_call_llm()` call — so the fallback activates only after all retries are exhausted. This is the correct layering: tenacity retries transient errors; `run_analysis()` catches persistent failures.

**DataFrame serialization choice** (Claude's discretion per context D-04):
Use `to_dict(orient="records")` for both `campaign_agg` and `merged_df`. Round-trips cleanly via `pd.DataFrame(payload["campaign_agg"])` without needing `orient` on load. Avoids the index-preservation issues of `to_json()`.

---

## Shared Patterns

### Postgres Connection
**Source:** `api/db.py` lines 10–15 (`get_conn()`)
**Apply to:** `st_db.py` — identical function, identical env var (`DATABASE_URL`), identical close-in-finally discipline.

### JSONB Serialization
**Source:** `api/db.py` line 68 — `Json(result.model_dump())`
**Apply to:** `st_db.py` — `Json(payload)` where `payload` is already a plain `dict` (no `.model_dump()` needed at the db layer; caller handles Pydantic serialization).

### `with conn: / with conn.cursor() as cur:` transaction pattern
**Source:** `api/db.py` throughout
**Apply to:** All functions in `st_db.py` — auto-commit on success, auto-rollback on exception, `conn.close()` in `finally`.

### `st.rerun()` after state mutation
**Source:** `app.py` lines 388, 530
**Apply to:** Load button handler and Delete button handler in sidebar Past Analyses section.

### `if k not in st.session_state:` guard
**Source:** `app.py` lines 143–145
**Apply to:** `"api_fallback_active"` key added to `_state_defaults` — same loop handles it automatically.

---

## No Analog Found

No files in this phase lack a codebase analog. All three files have strong matches.

---

## Metadata

**Analog search scope:** `api/db.py`, `app.py`, `llm.py`
**Files scanned:** 3
**Pattern extraction date:** 2026-06-04
