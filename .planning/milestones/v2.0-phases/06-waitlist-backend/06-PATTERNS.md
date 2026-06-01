# Phase 6: Waitlist Backend - Pattern Map

**Mapped:** 2026-06-01
**Files analyzed:** 6 new/modified files
**Analogs found:** 5 / 6 (one new module with no codebase analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `api/main.py` | controller | request-response | `api/main.py` (existing) | exact — extend in place |
| `api/db.py` | service | CRUD | `api/db.py` (existing) | exact — extend in place |
| `api/models.py` | model | request-response | `api/models.py` (existing) | exact — extend in place |
| `api/email_utils.py` | utility | request-response | no codebase analog | none — new pattern |
| `pyproject.toml` | config | — | `pyproject.toml` (existing) | exact — extend in place |
| `.env.example` | config | — | `.env.example` (existing) | exact — extend in place |

---

## Pattern Assignments

### `api/main.py` — extend: add CORSMiddleware + POST /api/waitlist

**Analog:** `api/main.py` (the file being modified)

**Imports pattern** (lines 1-14 of existing file):
```python
import logging
import os
import uuid
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

from api.db import get_latest_result, init_db, insert_analysis_result, insert_pending_session
from api.models import AnalyzeRequest, CrmWebhookRecord
from data import compute_campaign_agg
from llm import AnalysisResult, run_analysis
```

New imports to add (append to the import block):
```python
from fastapi.middleware.cors import CORSMiddleware
from api.db import insert_waitlist_email
from api.email_utils import send_waitlist_notification
from api.models import WaitlistRequest
```

**App instantiation + middleware placement** (lines 31-32 of existing file):
```python
app = FastAPI(lifespan=lifespan, title="Performance Plus API", version="2.0.0")
```

Insert immediately after `app = FastAPI(...)`, before any route decorators:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # D-11: wildcard for public credential-free endpoint
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Public endpoint pattern — no verify_api_key** (compare with protected endpoint at lines 59-62):

Protected (existing, do not change):
```python
@app.post("/api/webhook/crm", status_code=202)
def webhook_crm(record: CrmWebhookRecord, _: None = Depends(verify_api_key)):
    insert_pending_session(record)
    return {"status": "accepted"}
```

New public endpoint (no `Depends(verify_api_key)` per D-12):
```python
@app.post("/api/waitlist", status_code=200)
def waitlist_signup(body: WaitlistRequest):
    # insert_waitlist_email raises HTTPException(409) internally on duplicate (D-07)
    signed_up_at = insert_waitlist_email(body.email)
    try:
        send_waitlist_notification(body.email, signed_up_at)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SMTP error: {exc}")  # D-06
    return {"message": "You're on the waitlist! We'll be in touch."}
```

**Error handling pattern** (existing at lines 45-56):
```python
try:
    merged_df = pd.merge(web_df, crm_df, on=["session_id", "campaign_id"], how="inner", validate="m:1")
except pd.errors.MergeError as e:
    raise HTTPException(status_code=422, detail=f"Duplicate session_id in crm_records: {e}")
if merged_df.empty:
    raise HTTPException(status_code=422, detail="No session_id overlap between web_sessions and crm_records")
```

The waitlist handler follows the same `raise HTTPException(status_code=..., detail=...)` pattern. The 409 is raised inside `insert_waitlist_email` (not in the handler), and the 500 is raised in the handler's `except Exception` block.

---

### `api/db.py` — extend: add waitlist table + insert_waitlist_email + get_waitlist_entry

**Analog:** `api/db.py` (the file being modified)

**Imports pattern** (lines 1-5 of existing file):
```python
import os

import psycopg2
import psycopg2.extras  # required: Json adapter + JSONB auto-deserialization
from psycopg2.extras import Json
```

New import to add:
```python
import psycopg2.errors
from fastapi import HTTPException
```

**get_conn() pattern** (lines 8-10) — reuse unchanged:
```python
def get_conn():
    """Open a new connection. Caller is responsible for close()."""
    return psycopg2.connect(os.environ["DATABASE_URL"])
```

**init_db() table CREATE pattern** (lines 13-40) — add waitlist table alongside existing tables:
```python
def init_db() -> None:
    """Create tables if they don't exist. Called at lifespan startup."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        ...
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pending_sessions (
                        ...
                    )
                """)
                # ADD: waitlist table in the same with-block
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS waitlist (
                        id           SERIAL PRIMARY KEY,
                        email        TEXT NOT NULL UNIQUE,
                        signed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        source       TEXT NOT NULL DEFAULT 'landing_page'
                    )
                """)
    finally:
        conn.close()
```

**Core insert pattern** (lines 43-58 — insert_analysis_result):
```python
def insert_analysis_result(campaign_id: str, run_id: str, result) -> None:
    """Insert a campaign analysis result row into analysis_results."""
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

New `insert_waitlist_email` follows the same `conn / try / with conn / with conn.cursor() / finally conn.close()` structure, with two additions: `RETURNING signed_up_at` to retrieve the DB-generated timestamp, and `except psycopg2.errors.UniqueViolation` outside the `with conn:` block (so the context manager completes the rollback before the exception is caught):

```python
def insert_waitlist_email(email: str) -> str:
    """Insert email into waitlist. Returns signed_up_at as ISO string.
    Raises HTTPException(409) on duplicate email (D-07)."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO waitlist (email, source) VALUES (%s, %s) RETURNING signed_up_at",
                    (email, "landing_page"),
                )
                row = cur.fetchone()
                return row[0].isoformat()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="You're already on the waitlist.")
    finally:
        conn.close()
```

Critical: `except psycopg2.errors.UniqueViolation` must be placed OUTSIDE `with conn:` (after it closes, triggering rollback). Catching inside `with conn:` leaves the connection in an aborted transaction state.

**Core SELECT pattern** (lines 61-79 — get_latest_result):
```python
def get_latest_result(campaign_id: str) -> dict | None:
    """Return the most recent result_json for campaign_id, or None."""
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

New `get_waitlist_entry` follows the same pattern (SELECT WHERE, fetchone, return None if not found):
```python
def get_waitlist_entry(email: str) -> dict | None:
    """Return the waitlist row for email, or None if not present."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, signed_up_at, source FROM waitlist WHERE email = %s",
                    (email,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return {"id": row[0], "email": row[1], "signed_up_at": row[2].isoformat(), "source": row[3]}
    finally:
        conn.close()
```

---

### `api/models.py` — extend: add WaitlistRequest

**Analog:** `api/models.py` (the file being modified)

**Full existing file** (lines 1-32) — pattern to copy for new model:
```python
from pydantic import BaseModel


class WebSession(BaseModel):
    session_id: str
    campaign_id: str
    clicks: int
    impressions: int
    cost_usd: float
    conversion_rate: float


class CrmRecord(BaseModel):
    session_id: str
    campaign_id: str
    lead_status: str
    projected_value: float
    sales_notes: str


class AnalyzeRequest(BaseModel):
    web_sessions: list[WebSession]
    crm_records: list[CrmRecord]


class CrmWebhookRecord(BaseModel):
    session_id: str
    campaign_id: str
    lead_status: str
    projected_value: float
    sales_notes: str
```

New model appended at the bottom — only difference is `EmailStr` instead of `str` and the new import:
```python
from pydantic import BaseModel, EmailStr   # add EmailStr to existing pydantic import


class WaitlistRequest(BaseModel):
    email: EmailStr
```

`EmailStr` requires `email-validator` to be installed (not yet in `pyproject.toml`). Without it, `from pydantic import EmailStr` raises `ImportError` at app startup.

---

### `api/email_utils.py` — new file: SMTP notification helper

**Analog:** None — no existing module in the codebase uses `smtplib` or sends email. The pattern comes from the Python 3.11 stdlib.

**No codebase analog.** Use the verified pattern from RESEARCH.md Code Examples section directly:

```python
import os
import smtplib


def send_waitlist_notification(email: str, signed_up_at: str) -> None:
    """Send SMTP owner notification. Raises SMTPException on failure (D-06).

    Env vars required: SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS, SMTP_FROM.
    Recipient is hardcoded to info@k-innovative.com (D-04).
    """
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    from_addr = os.environ["SMTP_FROM"]
    to_addr = "info@k-innovative.com"

    subject = f"New waitlist signup: {email}"
    body = (
        "New signup on Performance Plus waitlist.\r\n\r\n"
        f"Email: {email}\r\n"
        f"Timestamp: {signed_up_at}\r\n"
        "Source: landing_page"
    )
    message = "\r\n".join([
        f"From: {from_addr}",
        f"To: {to_addr}",
        f"Subject: {subject}",
        "",
        body,
    ])
    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], message)
```

Key implementation notes:
- `os.environ["SMTP_HOST"]` (not `.get()`) raises `KeyError` if unset — intentional, surfaces misconfiguration immediately (D-06).
- `os.environ.get("SMTP_PORT", "587")` uses 587 as the default per D-02.
- `smtp.starttls()` before `smtp.login()` — STARTTLS negotiation must precede credential send (D-03).
- `with smtplib.SMTP(...) as smtp:` — context manager calls `QUIT` + `close()` on exit, including on exception.
- `signed_up_at` is a string (ISO format from `insert_waitlist_email`), not a `datetime` object — avoids ugly `repr()` in the email body.

---

### `pyproject.toml` — extend: add email-validator dependency

**Analog:** `pyproject.toml` (the file being modified, lines 1-16)

**Existing dependencies block** (lines 6-16):
```toml
dependencies = [
  "streamlit>=1.40,<2.0",
  "pandas>=2.2.3,<2.3",
  "python-dotenv>=1.0",
  "openai>=1.50,<2.0",
  "pydantic>=2.8,<3.0",
  "tenacity>=8.5",
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.29,<1.0",
  "psycopg2-binary>=2.9,<3.0",
]
```

Add `email-validator` at the end of the list:
```toml
  "email-validator>=2.0,<3.0",
```

Install via: `uv add "email-validator>=2.0,<3.0"` (updates both `pyproject.toml` and `uv.lock`).

---

### `.env.example` — extend: add 5 SMTP vars

**Analog:** `.env.example` (the file being modified)

**Existing file** (all 5 lines):
```
OPENAI_API_KEY=your-key-here
DEMO_MODE=
API_KEY=your-api-key-here
DATABASE_URL=postgresql://ppuser:password@postgres:5432/performance_plus
POSTGRES_PASSWORD=your-postgres-password-here
```

Append 5 new SMTP vars:
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASS=your-smtp-password
SMTP_FROM=noreply@example.com
```

Note: `SMTP_FROM` may differ from `SMTP_USER` (D-02 — shared mailbox scenario). All five must be present in `.env` for `send_waitlist_notification` to function. `SMTP_PORT` has a default of 587 in code but should still be set explicitly in `.env` for clarity.

---

## Shared Patterns

### psycopg2 connection lifecycle
**Source:** `api/db.py` lines 8-10, 43-58
**Apply to:** All new `api/db.py` functions (`insert_waitlist_email`, `get_waitlist_entry`)
```python
conn = get_conn()
try:
    with conn:
        with conn.cursor() as cur:
            cur.execute("...", (param,))
            # fetchone() if SELECT or RETURNING
finally:
    conn.close()
```
The `with conn:` block commits on clean exit and rolls back on exception. The outer `try/finally` ensures `conn.close()` is always called. Never use f-string interpolation in SQL — always use `%s` parameterized placeholders.

### HTTPException error mapping
**Source:** `api/main.py` lines 45-56, `api/db.py` (new insert_waitlist_email)
**Apply to:** `api/main.py` waitlist handler, `api/db.py` insert_waitlist_email
```python
raise HTTPException(status_code=409, detail="You're already on the waitlist.")
raise HTTPException(status_code=500, detail=f"SMTP error: {exc}")
raise HTTPException(status_code=404, detail=f"No analysis results found for campaign_id={campaign_id}")
```
`HTTPException` is raised directly — no custom exception classes. `detail` is a plain string. This is the existing project convention throughout `api/main.py`.

### Test monkeypatch binding rule
**Source:** `tests/test_api.py` lines 62-86 (`_make_client` factory)
**Apply to:** All new tests in `tests/test_api.py` for Phase 6
```python
def _make_client(monkeypatch, db_overrides=None):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setattr("llm.client", None)
    monkeypatch.setattr("api.main.init_db", lambda: None)
    if db_overrides:
        for name, mock in db_overrides.items():
            monkeypatch.setattr(f"api.main.{name}", mock)
    from api.main import app  # noqa: PLC0415 — intentional deferred import
    return TestClient(app)
```
**Critical rule:** Patch `api.main.insert_waitlist_email` and `api.main.send_waitlist_notification`, NOT `api.db.insert_waitlist_email` or `api.email_utils.send_waitlist_notification`. The `from ... import` in `api/main.py` creates local bindings; patching the source module after the import has no effect on those bindings.

### Env var access pattern
**Source:** `api/db.py` line 10, `api/main.py` line 21
**Apply to:** `api/email_utils.py`
```python
os.environ["DATABASE_URL"]  # KeyError if unset — intentional, surfaces misconfiguration
os.environ.get("API_KEY")   # None if unset — used when absence is acceptable
```
Use `os.environ["KEY"]` (not `.get()`) for required vars that must be set for the service to function. `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` are required — use bracket access. `SMTP_PORT` has a safe default — use `.get("SMTP_PORT", "587")`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `api/email_utils.py` | utility | request-response | No existing module in the codebase uses `smtplib` or sends any email. Use RESEARCH.md Pattern 3 (smtplib STARTTLS) directly. |

---

## Metadata

**Analog search scope:** `api/`, `tests/`, project root config files
**Files scanned:** `api/db.py` (104 lines), `api/main.py` (71 lines), `api/models.py` (32 lines), `tests/test_api.py` (405 lines), `pyproject.toml` (28 lines), `.env.example` (5 lines)
**Pattern extraction date:** 2026-06-01
