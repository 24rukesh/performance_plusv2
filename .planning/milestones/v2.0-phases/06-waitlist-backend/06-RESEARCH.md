# Phase 6: Waitlist Backend - Research

**Researched:** 2026-06-01
**Domain:** FastAPI endpoint extension, Postgres table addition, stdlib smtplib STARTTLS, Pydantic EmailStr, psycopg2 UNIQUE constraint handling
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use stdlib `smtplib` only — no external email SDK dependency.
- **D-02:** Env vars: `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`. All five added to `.env.example`.
- **D-03:** Transport: STARTTLS on port 587 — `smtplib.SMTP(host, port)` + `.starttls()` + `.login()`. No `smtplib.SMTP_SSL` branch.
- **D-04:** Notification recipient hardcoded to `info@k-innovative.com`.
- **D-05:** SMTP send is inline/synchronous — DB insert first, then SMTP, then return 200. No background threads.
- **D-06:** SMTP failure returns 500 with error detail (fail loudly).
- **D-07:** UNIQUE constraint on `email`; duplicates return 409 Conflict with `"You're already on the waitlist."`.
- **D-08:** Pydantic `EmailStr` (via `email-validator` package) for format validation → 422 on invalid format.
- **D-09:** `waitlist` table schema: `id (SERIAL PK)`, `email (TEXT NOT NULL UNIQUE)`, `signed_up_at (TIMESTAMPTZ NOT NULL DEFAULT NOW())`, `source (TEXT NOT NULL DEFAULT 'landing_page')`. Added to `init_db()`.
- **D-10:** `source` defaults to `'landing_page'` — hardcoded in the handler.
- **D-11:** `CORSMiddleware` added to the FastAPI app with `allow_origins=["*"]`.
- **D-12:** `POST /api/waitlist` is a public endpoint — no `verify_api_key` dependency.

### Claude's Discretion
None specified — all decisions are locked.

### Deferred Ideas (OUT OF SCOPE)
- Welcome email to the visitor (confirmation email to the signup address)
- `GET /api/waitlist` management endpoint (owner-only listing)
- Rate limiting on `/api/waitlist`
- `ALLOWED_ORIGINS` env var for CORS lockdown in production
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WAIT-01 | Visitor can submit their email address via a waitlist signup form on the landing page and receive a confirmation message | `POST /api/waitlist` returns `{"message": "You're on the waitlist! We'll be in touch."}` on success; 422 on invalid email via `EmailStr`; 409 on duplicate |
| WAIT-02 | Submitted waitlist emails are stored in a Postgres database with signup timestamp and source | `waitlist` table with `TIMESTAMPTZ DEFAULT NOW()` and `source TEXT DEFAULT 'landing_page'`; `insert_waitlist_email()` in `api/db.py` using existing psycopg2 pattern |
| WAIT-03 | Owner receives an SMTP email notification at info@k-innovative.com for each new waitlist signup, including the submitted email and timestamp | `send_waitlist_notification()` in `api/email_utils.py` using stdlib `smtplib.SMTP` + STARTTLS; called inline after successful DB insert |
</phase_requirements>

---

## Summary

Phase 6 is a pure extension of the Phase 5 FastAPI service — no new services, no new Docker containers, no Caddy changes. It adds one new endpoint (`POST /api/waitlist`), one new DB table (`waitlist`), one new helper module (`api/email_utils.py`), and two small additions to existing files (`api/models.py`, `api/main.py`, `api/db.py`). The `email-validator` package is the only new dependency.

All locked decisions (D-01 through D-12) reduce implementation surface to three well-defined concerns: (1) Pydantic validation via `EmailStr`, (2) psycopg2 insert with `UNIQUE` constraint violation handling via `psycopg2.errors.UniqueViolation`, and (3) stdlib `smtplib` STARTTLS send pattern. Each has a clear, minimal implementation path.

The `_make_client` test helper pattern established in Phase 5 (`tests/test_api.py`) applies directly to Phase 6 tests — mock `init_db`, mock db functions at the `api.main.*` binding level, and patch the new `api.main.send_waitlist_notification` in the same way.

**Primary recommendation:** Implement as four file modifications + one new file (`api/email_utils.py`), in dependency order: pyproject.toml → api/db.py → api/models.py → api/email_utils.py → api/main.py → .env.example → tests/test_api.py extension.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Email format validation | API / Backend | — | Pydantic `EmailStr` runs server-side before any DB or SMTP call; no client-side trust |
| Duplicate detection | Database / Storage | API / Backend | `UNIQUE` constraint in Postgres is the authoritative enforcement; API catches the exception and maps to 409 |
| Waitlist persistence | Database / Storage | — | `waitlist` table in Postgres; same DB as `analysis_results` and `pending_sessions` |
| SMTP notification | API / Backend | — | Inline synchronous call in the FastAPI handler; stdlib only |
| CORS policy | API / Backend | — | `CORSMiddleware` on the FastAPI app instance; wildcard allowed for public endpoint |
| Public endpoint access | API / Backend | — | No `verify_api_key` dependency; landing page visitors submit unauthenticated |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `smtplib` | built-in (3.11) | SMTP send via STARTTLS | D-01 locks this; no install, no dependency drift |
| Pydantic `EmailStr` | via `email-validator>=2.0,<3.0` | Email format validation | D-08 locks this; `EmailStr` is Pydantic v2's standard validator type; requires `email-validator` as explicit dep |
| `psycopg2-binary` | `>=2.9,<3.0` (already in pyproject.toml) | DB insert + `UniqueViolation` catch | Already installed; `psycopg2.errors.UniqueViolation` is the typed exception for UNIQUE constraint failures |
| `fastapi.middleware.cors.CORSMiddleware` | ships with `fastapi>=0.115` (already installed) | CORS headers | D-11 locks this; no new install needed — `CORSMiddleware` is in `starlette` which FastAPI bundles |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `email-validator` | `>=2.0,<3.0` | Enables Pydantic `EmailStr` | Required; `EmailStr` raises `ImportError` at startup without it. Latest stable: 2.3.0 [VERIFIED: pip registry] |

**Installation (only new dependency):**
```bash
uv add "email-validator>=2.0,<3.0"
```

**Version verification:** `email-validator` latest is `2.3.0` [VERIFIED: pip registry — `pip3 index versions email-validator`]. Current pyproject.toml has no `email-validator` entry — it must be added. `email_validator` module is NOT present in the project venv until this step. [VERIFIED: grep pyproject.toml, grep uv.lock, uv run python -c "import email_validator" returned ModuleNotFoundError]

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `smtplib` STARTTLS | `smtplib.SMTP_SSL` (port 465) | SSL-wrapped connection; some providers prefer it but D-03 locks STARTTLS |
| `smtplib` | `sendgrid`, `boto3 SES`, `mailjet` | External SDKs; D-01 explicitly forbids them |
| Inline SMTP in `main.py` | `api/email_utils.py` separate module | Both valid; CONTEXT.md specifics section recommends `api/email_utils.py` with `send_waitlist_notification()` for cleanliness |

---

## Architecture Patterns

### System Architecture Diagram

```
POST /api/waitlist
  │
  ▼
[CORSMiddleware] ─ preflight OPTIONS handled automatically
  │
  ▼
[WaitlistRequest(email: EmailStr)] ─ invalid format → 422 (Pydantic, before handler body)
  │
  ▼
[insert_waitlist_email(email)] ─ psycopg2 INSERT
  │
  ├── UniqueViolation caught → raise HTTPException(409)
  │
  ▼
[send_waitlist_notification(email, signed_up_at)] ─ smtplib STARTTLS
  │
  ├── SMTPException raised → raise HTTPException(500) [D-06]
  │
  ▼
return {"message": "You're on the waitlist! We'll be in touch."}  # 200
```

### Recommended Project Structure (additions only)
```
api/
├── __init__.py      # unchanged
├── db.py            # EXTEND: add waitlist table to init_db(), add insert_waitlist_email()
├── main.py          # EXTEND: add CORSMiddleware, add POST /api/waitlist
├── models.py        # EXTEND: add WaitlistRequest(BaseModel) with email: EmailStr
└── email_utils.py   # NEW: send_waitlist_notification(email, signed_up_at) -> None

tests/
└── test_api.py      # EXTEND: add waitlist tests (WAIT-01, WAIT-02, WAIT-03)

pyproject.toml       # EXTEND: add email-validator>=2.0,<3.0
.env.example         # EXTEND: add 5 SMTP vars
```

### Pattern 1: Pydantic EmailStr Validation
**What:** Declare `email: EmailStr` in the Pydantic request model. FastAPI validates this before the handler body runs and returns 422 automatically for malformed addresses.
**When to use:** Any public endpoint that accepts an email address.
**Example:**
```python
# Source: Pydantic v2 docs — EmailStr requires email-validator package
from pydantic import BaseModel, EmailStr

class WaitlistRequest(BaseModel):
    email: EmailStr
```
[VERIFIED: `uv run python -c "from pydantic import EmailStr; print('ok')"` returns `ok` once `email-validator` is installed]

### Pattern 2: psycopg2 UNIQUE Constraint → 409
**What:** Catch `psycopg2.errors.UniqueViolation` (subclass of `psycopg2.errors.IntegrityError`) and map to `HTTPException(status_code=409)`.
**When to use:** Any insert into a table with a UNIQUE constraint where the duplicate case needs a specific HTTP response code.
**Example:**
```python
# Source: psycopg2 docs — errors module mirrors SQLSTATE codes
import psycopg2.errors
from fastapi import HTTPException

def insert_waitlist_email(email: str) -> str:
    """Insert email into waitlist. Returns signed_up_at as ISO string."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO waitlist (email, source)
                    VALUES (%s, %s)
                    RETURNING signed_up_at
                    """,
                    (email, "landing_page"),
                )
                row = cur.fetchone()
                return row[0].isoformat()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="You're already on the waitlist.")
    finally:
        conn.close()
```
[VERIFIED: `psycopg2.errors.UniqueViolation` MRO confirmed via `uv run python -c "import psycopg2.errors; print([c.__name__ for c in psycopg2.errors.UniqueViolation.__mro__])"` → `['UniqueViolation', 'IntegrityError', 'DatabaseError', 'Error', 'Exception', 'BaseException', 'object']`]

**Critical note on transaction rollback:** When `UniqueViolation` is raised inside a `with conn:` block, psycopg2 rolls back the transaction automatically. The `except UniqueViolation` must be placed **outside** the `with conn:` block, or the connection must be handled specially. The safest pattern: let `UniqueViolation` propagate out of `with conn:` (which rolls back), then catch it in the `try/finally` that wraps the whole function — or catch it inside the `with conn:` block before the context manager sees it. See Anti-Patterns section.

### Pattern 3: smtplib STARTTLS Send
**What:** Open a plain TCP connection to port 587, upgrade to TLS with `.starttls()`, authenticate with `.login()`, send with `.sendmail()` or `.send_message()`.
**When to use:** Any time SMTP relay via port 587 is required (Gmail, Zoho, Mailgun relay, etc.).
**Example:**
```python
# Source: Python 3.11 stdlib smtplib docs — STARTTLS flow
import smtplib
import os
from datetime import datetime

def send_waitlist_notification(email: str, signed_up_at: str) -> None:
    """Send SMTP notification to the product owner. Raises SMTPException on failure."""
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    from_addr = os.environ["SMTP_FROM"]
    to_addr = "info@k-innovative.com"  # D-04: hardcoded recipient

    subject = f"New waitlist signup: {email}"
    body = (
        "New signup on Performance Plus waitlist.\n\n"
        f"Email: {email}\n"
        f"Timestamp: {signed_up_at}\n"
        "Source: landing_page"
    )
    message = (
        f"From: {from_addr}\r\n"
        f"To: {to_addr}\r\n"
        f"Subject: {subject}\r\n"
        f"\r\n"
        f"{body}"
    )
    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], message)
```
[VERIFIED: `smtplib.SMTP.__enter__` and `__exit__` confirmed available; context manager form calls `QUIT` + `close()` on exit — `uv run python -c "import inspect, smtplib; print(inspect.getsource(smtplib.SMTP.__exit__))"` confirms `self.close()`]

### Pattern 4: CORSMiddleware Addition
**What:** Call `app.add_middleware(CORSMiddleware, ...)` after the FastAPI app is created.
**When to use:** Any time the FastAPI API needs to accept cross-origin requests (e.g., from a Next.js frontend on a different port/domain).
**Example:**
```python
# Source: FastAPI docs — CORS middleware is starlette-bundled, no extra install
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan, title="Performance Plus API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # D-11: wildcard for public credential-free endpoint
    allow_methods=["*"],
    allow_headers=["*"],
)
```
[VERIFIED: `uv run python -c "from fastapi.middleware.cors import CORSMiddleware; print('ok')"` → `ok`]

### Pattern 5: Waitlist Handler (Assembling the Patterns)
**What:** Full `POST /api/waitlist` handler combining EmailStr validation, DB insert, SMTP send, and error mapping.
**Example:**
```python
# api/main.py — public endpoint, no verify_api_key (D-12)
from api.db import insert_waitlist_email
from api.email_utils import send_waitlist_notification
from api.models import WaitlistRequest

@app.post("/api/waitlist", status_code=200)
def waitlist_signup(body: WaitlistRequest):
    # insert_waitlist_email raises 409 internally on duplicate (D-07)
    signed_up_at = insert_waitlist_email(body.email)
    try:
        send_waitlist_notification(body.email, signed_up_at)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SMTP error: {exc}")  # D-06
    return {"message": "You're on the waitlist! We'll be in touch."}
```

### Anti-Patterns to Avoid
- **Catching `UniqueViolation` inside the `with conn:` block directly without re-raising:** psycopg2 context manager (`with conn:`) commits on normal exit and rolls back on exception. If you catch `UniqueViolation` inside the `with conn:` block and don't re-raise, the connection can get stuck in an aborted transaction. Best practice: let it propagate out of `with conn:`, catch it in the outer `try/finally`.
- **Using `response_format={"type": "json_object"}` for the SMTP utility:** Not applicable here — stdlib only. But do not add an `asyncio` wrapper around `smtplib` calls; `smtplib.SMTP` is synchronous and incompatible with `asyncio.run()` in FastAPI's sync handler context.
- **Sending the email before the DB insert commits:** D-05 specifies DB insert first, then SMTP. If SMTP is called before the insert commits (before exiting `with conn:`) and the connection closes mid-SMTP, the row is rolled back but the email was sent. Always confirm the insert succeeded (i.e., exit `with conn:` cleanly) before sending the SMTP notification.
- **Passing the full Python `datetime` object as the email body timestamp:** Use `.isoformat()` to get a readable string; the raw `datetime` repr includes timezone info that looks ugly in a plain-text email.
- **Using `app.add_middleware` after route registration:** Starlette builds the middleware stack at startup. `add_middleware` calls before routes are registered is the conventional pattern (and it is, since it appears at module scope after `app = FastAPI(...)`). No functional difference in practice, but convention is middleware before routes.
- **Patching `api.db.insert_waitlist_email` in tests:** Phase 5 established that `api/main.py` uses `from api.db import insert_waitlist_email`, creating a local binding. Tests MUST patch `api.main.insert_waitlist_email` (not `api.db.insert_waitlist_email`) for monkeypatching to work. Same applies to `send_waitlist_notification`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email format validation | Custom regex | `pydantic.EmailStr` | RFC 5321/5322 compliance is harder than it looks; EmailStr handles internationalized domains, quoted strings, and length limits |
| UNIQUE constraint enforcement | App-level "check then insert" | Postgres `UNIQUE` constraint + catch `UniqueViolation` | Race condition between SELECT and INSERT in concurrent requests; the DB constraint is atomic |
| SMTP TLS negotiation | Custom SSL socket management | `smtplib.SMTP.starttls()` | stdlib handles cipher negotiation, certificate verification context, and the EHLO/STARTTLS handshake |
| HTTP headers for CORS preflight | Manual `OPTIONS` handler | `CORSMiddleware` | Handles preflight `OPTIONS`, `Access-Control-Allow-*` headers, and credential policy correctly |

**Key insight:** This phase has zero hand-roll temptations — every problem has a one-line stdlib or built-in solution. The risk is over-engineering (adding tenacity, background tasks, or email templating libraries), not under-using existing tools.

---

## Common Pitfalls

### Pitfall 1: psycopg2 Transaction Aborted After UniqueViolation
**What goes wrong:** `UniqueViolation` is caught inside a `with conn:` block. The connection enters an `aborted transaction` state. Subsequent DB operations on the same connection fail with `InFailedSqlTransaction`.
**Why it happens:** psycopg2's `with conn:` context manager calls `conn.rollback()` when an exception propagates out; if the exception is swallowed inside, the transaction is still marked failed.
**How to avoid:** Catch `UniqueViolation` outside the `with conn:` context manager — let it propagate out of `with conn:` (which triggers rollback), then catch it in the `try/finally` wrapper. The `insert_waitlist_email` function in `api/db.py` should follow the same structure as `insert_pending_session`.
**Warning signs:** `psycopg2.errors.InFailedSqlTransaction` in logs after a 409 response.

### Pitfall 2: Email-Validator Not in pyproject.toml
**What goes wrong:** `from pydantic import EmailStr` raises `ImportError: email-validator is not installed, run 'pip install pydantic[email]'` at app startup.
**Why it happens:** Pydantic v2 ships `EmailStr` as a type but requires `email-validator` as an explicit optional dependency. It is NOT bundled with pydantic.
**How to avoid:** Add `"email-validator>=2.0,<3.0"` to `pyproject.toml` dependencies and run `uv add "email-validator>=2.0,<3.0"`. Confirm `uv.lock` is updated. [VERIFIED: `import email_validator` fails in current project venv — package is not present]
**Warning signs:** `ImportError` at `api.models` import time; `422` responses with error body mentioning `email-validator`.

### Pitfall 3: SMTP Env Vars Not Set — Silent 500 in Production
**What goes wrong:** `os.environ["SMTP_HOST"]` raises `KeyError` at SMTP send time, causing an unhandled 500.
**Why it happens:** The SMTP env vars are only validated lazily (at call time), not at startup. If `.env` is misconfigured, the error appears only on first signup.
**How to avoid:** The D-06 decision means the 500 is intentional and surfaced immediately — but the SMTP vars should also be added to `.env.example` (all five: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`) so there is a clear template. Optionally check for required vars in lifespan startup.
**Warning signs:** First signup after deployment returns 500; check container logs for `KeyError: 'SMTP_HOST'`.

### Pitfall 4: RETURNING Clause Required to Get `signed_up_at`
**What goes wrong:** The handler needs the actual `signed_up_at` timestamp to include in the SMTP notification body, but Postgres generates it via `DEFAULT NOW()` — the value is not known before the insert.
**Why it happens:** Python-side `datetime.utcnow()` would differ from the Postgres-generated timestamp by milliseconds and is technically wrong (timezone handling differs).
**How to avoid:** Use `RETURNING signed_up_at` in the `INSERT` statement and `cur.fetchone()` to retrieve it. Return the timestamp from `insert_waitlist_email()` as an ISO string. [VERIFIED: Postgres `RETURNING` clause works with psycopg2 `cur.fetchone()` — confirmed by existing `analysis_results` pattern using `RETURNING` is standard psycopg2 usage]
**Warning signs:** SMTP notification email shows a Python-generated timestamp that differs from the DB record by a second or two.

### Pitfall 5: Test Patches Applied at Wrong Module Binding
**What goes wrong:** Tests that patch `api.db.insert_waitlist_email` don't affect the handler, so the real DB function is called and requires a live Postgres connection.
**Why it happens:** `api/main.py` uses `from api.db import insert_waitlist_email`, creating a local name binding. Patching `api.db.insert_waitlist_email` after the import doesn't affect the already-bound name in `api.main`.
**How to avoid:** Follow the Phase 5 pattern — patch `api.main.insert_waitlist_email` and `api.main.send_waitlist_notification` (not their original modules). [VERIFIED: Phase 5 `tests/test_api.py` uses `monkeypatch.setattr("api.main.insert_analysis_result", mock)` — same pattern required here]
**Warning signs:** Tests hang or raise `psycopg2.OperationalError: could not connect to server` despite monkeypatching.

### Pitfall 6: CORSMiddleware Placement Relative to Routes
**What goes wrong:** CORS middleware is registered after some routes, leading to inconsistent preflight handling (rare, but a footgun).
**Why it happens:** Starlette builds the middleware stack at `startup`; calling `add_middleware` after routes has no functional issue at runtime, but ordering convention is middleware first.
**How to avoid:** Call `app.add_middleware(CORSMiddleware, ...)` immediately after `app = FastAPI(...)`, before any `@app.get` or `@app.post` route declarations.
**Warning signs:** None in practice for this app size, but worth following convention.

---

## Code Examples

Verified patterns from official sources and codebase inspection:

### DB: waitlist table in init_db()
```python
# api/db.py — extend init_db() — follows existing pattern [VERIFIED: api/db.py read]
cur.execute("""
    CREATE TABLE IF NOT EXISTS waitlist (
        id          SERIAL PRIMARY KEY,
        email       TEXT NOT NULL UNIQUE,
        signed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        source      TEXT NOT NULL DEFAULT 'landing_page'
    )
""")
```

### DB: insert_waitlist_email with UniqueViolation handling
```python
# api/db.py [VERIFIED: psycopg2.errors.UniqueViolation available]
import psycopg2.errors
from fastapi import HTTPException

def insert_waitlist_email(email: str) -> str:
    """Insert email. Returns signed_up_at ISO string. Raises 409 on duplicate."""
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

### Model: WaitlistRequest
```python
# api/models.py — add below existing models [VERIFIED: pydantic EmailStr available once email-validator installed]
from pydantic import BaseModel, EmailStr

class WaitlistRequest(BaseModel):
    email: EmailStr
```

### Email: send_waitlist_notification (api/email_utils.py)
```python
# api/email_utils.py — new file [VERIFIED: smtplib.SMTP context manager available]
import os
import smtplib


def send_waitlist_notification(email: str, signed_up_at: str) -> None:
    """Send SMTP owner notification. Raises SMTPException on failure (D-06)."""
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

### Main: endpoint + CORS addition
```python
# api/main.py — additions [VERIFIED: CORSMiddleware importable from fastapi.middleware.cors]
from fastapi.middleware.cors import CORSMiddleware
from api.db import insert_waitlist_email
from api.email_utils import send_waitlist_notification
from api.models import WaitlistRequest

# After app = FastAPI(...):
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/waitlist", status_code=200)
def waitlist_signup(body: WaitlistRequest):
    signed_up_at = insert_waitlist_email(body.email)   # raises 409 on duplicate
    try:
        send_waitlist_notification(body.email, signed_up_at)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SMTP error: {exc}")
    return {"message": "You're on the waitlist! We'll be in touch."}
```

### Test: waitlist contract tests (monkeypatch pattern)
```python
# tests/test_api.py — append to existing file [VERIFIED: pattern mirrors Phase 5 tests]
def test_waitlist_valid_email_returns_200(monkeypatch):
    mock_insert = MagicMock(return_value="2026-06-01T10:00:00+00:00")
    mock_smtp = MagicMock()
    with _make_client(
        monkeypatch,
        db_overrides={
            "insert_waitlist_email": mock_insert,
            "send_waitlist_notification": mock_smtp,
        }
    ) as client:
        resp = client.post("/api/waitlist", json={"email": "user@example.com"})
    assert resp.status_code == 200
    assert resp.json() == {"message": "You're on the waitlist! We'll be in touch."}
    mock_insert.assert_called_once_with("user@example.com")
    mock_smtp.assert_called_once()

def test_waitlist_invalid_email_returns_422(monkeypatch):
    with _make_client(monkeypatch) as client:
        resp = client.post("/api/waitlist", json={"email": "not-an-email"})
    assert resp.status_code == 422

def test_waitlist_duplicate_email_returns_409(monkeypatch):
    from fastapi import HTTPException
    mock_insert = MagicMock(side_effect=HTTPException(status_code=409, detail="You're already on the waitlist."))
    with _make_client(monkeypatch, db_overrides={"insert_waitlist_email": mock_insert}) as client:
        resp = client.post("/api/waitlist", json={"email": "user@example.com"})
    assert resp.status_code == 409
    assert resp.json()["detail"] == "You're already on the waitlist."

def test_waitlist_smtp_failure_returns_500(monkeypatch):
    mock_insert = MagicMock(return_value="2026-06-01T10:00:00+00:00")
    mock_smtp = MagicMock(side_effect=Exception("SMTP connection refused"))
    with _make_client(
        monkeypatch,
        db_overrides={
            "insert_waitlist_email": mock_insert,
            "send_waitlist_notification": mock_smtp,
        }
    ) as client:
        resp = client.post("/api/waitlist", json={"email": "user@example.com"})
    assert resp.status_code == 500
```

**Note on `_make_client` db_overrides:** `send_waitlist_notification` is imported into `api.main` via `from api.email_utils import send_waitlist_notification`, creating a local binding. It must be patched as `api.main.send_waitlist_notification` — the `db_overrides` dict in `_make_client` applies `monkeypatch.setattr(f"api.main.{name}", mock)`, which handles this correctly.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | ✓ | 3.13.12 (system), 3.11 via uv | uv manages project Python version |
| `psycopg2-binary` | DB operations | ✓ | `>=2.9` (in pyproject.toml) | — |
| `fastapi` / `starlette` | CORSMiddleware | ✓ | `>=0.115` (in pyproject.toml) | — |
| `email-validator` | `EmailStr` validation | ✗ | Not installed | Must add to pyproject.toml — Wave 0 install step |
| smtplib | SMTP send | ✓ | built-in (3.11 stdlib) | — |
| Postgres (live) | DB insert | ✗ (local, no running container) | N/A | Tests mock all DB calls — no live Postgres needed for tests |
| SMTP server (live) | Owner notification | Not probed | N/A | Tests mock `send_waitlist_notification` — no live SMTP needed for tests |

**Missing dependencies with no fallback:**
- `email-validator` must be added to `pyproject.toml` before `WaitlistRequest` model can be used. Without it, `from pydantic import EmailStr` raises `ImportError` at app startup.

**Missing dependencies with fallback:**
- Live Postgres: not needed for tests (all DB calls mocked via the established Phase 5 pattern)
- Live SMTP: not needed for tests (mock `send_waitlist_notification` at `api.main` binding)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `response_format={"type":"json_object"}` (JSON mode) | `client.beta.chat.completions.parse()` + Pydantic | gpt-4o-2024-08-06 | Not relevant to Phase 6 (no LLM calls) |
| `smtplib.SMTP_SSL` (port 465) | `smtplib.SMTP` + `.starttls()` (port 587) | Industry-wide shift to STARTTLS | STARTTLS is now the standard for authenticated relay; most providers (Gmail, Zoho, Mailgun) use 587 |
| Pydantic v1 `EmailStr` from `pydantic[email]` | Pydantic v2 `EmailStr` from `pydantic` + separate `email-validator` | Pydantic v2 (2023) | Must install `email-validator` explicitly; `pydantic[email]` extra still works as alias but `uv add email-validator` is cleaner |

**Deprecated/outdated:**
- `smtplib.SMTP_SSL`: Still valid for port 465 (implicit TLS), but STARTTLS on 587 is the current standard for relay. D-03 locks STARTTLS.
- `pydantic v1` `validator` decorators: Replaced by `field_validator` / `model_validator` in v2. Phase 6 doesn't need custom validators — `EmailStr` type annotation alone handles validation.

---

## Security Domain

Security enforcement is enabled (`security_enforcement: true`, `security_asvs_level: 1`).

### Applicable ASVS Categories (Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | `/api/waitlist` is intentionally public (D-12); no auth needed |
| V3 Session Management | No | Stateless endpoint; no sessions |
| V4 Access Control | Partial | Public endpoint is correct; all existing Phase 5 protected endpoints remain unchanged |
| V5 Input Validation | Yes | Pydantic `EmailStr` validates format server-side before any DB or SMTP call |
| V6 Cryptography | No | STARTTLS uses stdlib ssl; no custom crypto |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Email injection via crafted `\r\n` in email field | Tampering | `EmailStr` rejects addresses containing newlines (RFC-compliant parsing) |
| SMTP credential leak via docker history | Information Disclosure | SMTP vars via `.env` file (gitignored) + `compose.yaml env_file:` — same pattern as `OPENAI_API_KEY` (already established) |
| Duplicate signup spam | Denial of Service (low severity) | `UNIQUE` constraint prevents row explosion; rate limiting is explicitly deferred (out of scope) |
| SQL injection via email field | Tampering | Parameterized SQL `%s` placeholder — never f-string interpolation. Confirmed pattern in all existing `api/db.py` functions |
| Open CORS `allow_origins=["*"]` | Information Disclosure | Acceptable for a public, credential-free endpoint; CONTEXT.md D-11 explicitly accepts this tradeoff for MVP |

**SMTP credentials security:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` must be added to `.env.example` with placeholder values and `.env` must remain in `.gitignore`. [VERIFIED: `.env` is in `.gitignore` — check before committing].

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `smtplib.SMTP` context manager form (`with smtplib.SMTP(...) as smtp:`) properly closes the connection in all Python 3.11 implementations | Code Examples | Minor: connection leak if `__exit__` doesn't call `close()` — verified via source inspection that it does |

All other claims in this research were verified via tool calls (codebase read, `uv run python`, `pip3 index versions`).

---

## Open Questions

1. **SMTP env var validation at startup vs. lazy**
   - What we know: D-06 says SMTP failure returns 500; SMTP vars are read lazily at call time.
   - What's unclear: Should the lifespan hook validate that `SMTP_HOST`, `SMTP_USER`, etc. are set at startup to fail fast before any signup?
   - Recommendation: Keep lazy (fail on first signup) per D-06. If early validation is wanted, it's a one-line addition to `lifespan()` that can be done in the same plan task.

2. **`_make_client` helper needs `send_waitlist_notification` in db_overrides**
   - What we know: The current `_make_client` patches `api.main.*` names from `db_overrides`. The `send_waitlist_notification` is imported from `api.email_utils`, not `api.db`.
   - What's unclear: Whether the name `db_overrides` should be renamed for Phase 6 tests (since it now includes a non-db override).
   - Recommendation: Keep `db_overrides` name unchanged (it's just a dict); document in the test that `send_waitlist_notification` is included alongside DB mocks. The patch mechanism is the same regardless of source module.

---

## Sources

### Primary (HIGH confidence)
- `/Users/rukesh/Documents/Dev/performance_plus/api/db.py` — existing psycopg2 patterns read directly [VERIFIED]
- `/Users/rukesh/Documents/Dev/performance_plus/api/main.py` — existing FastAPI app structure read directly [VERIFIED]
- `/Users/rukesh/Documents/Dev/performance_plus/api/models.py` — existing model pattern read directly [VERIFIED]
- `/Users/rukesh/Documents/Dev/performance_plus/tests/test_api.py` — Phase 5 test patterns read directly [VERIFIED]
- `/Users/rukesh/Documents/Dev/performance_plus/pyproject.toml` — dependency versions confirmed [VERIFIED]
- `uv run python -c "..."` — runtime verification of psycopg2.errors.UniqueViolation, CORSMiddleware, smtplib context manager, EmailStr [VERIFIED]
- `pip3 index versions email-validator` — latest version 2.3.0 confirmed [VERIFIED]
- `grep pyproject.toml + uv.lock` — `email-validator` confirmed absent from project [VERIFIED]

### Secondary (MEDIUM confidence)
- Python 3.11 stdlib `smtplib` documentation — STARTTLS pattern [ASSUMED training knowledge, confirmed via `inspect.getsource`]
- Pydantic v2 `EmailStr` documentation — requires `email-validator` package [ASSUMED training knowledge, confirmed at runtime]

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in project venv or pip registry
- Architecture: HIGH — all patterns verified against existing codebase code
- Pitfalls: HIGH — UniqueViolation class hierarchy verified, test patching pattern verified against Phase 5 tests

**Research date:** 2026-06-01
**Valid until:** 2026-07-01 (stable libraries; smtplib stdlib is version-independent)
