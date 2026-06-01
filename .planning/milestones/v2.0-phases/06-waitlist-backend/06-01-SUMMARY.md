---
phase: 06-waitlist-backend
plan: "01"
subsystem: api
tags: [postgres, pydantic, email-validator, smtplib, psycopg2, fastapi]

requires:
  - phase: 05-fastapi-service
    provides: FastAPI app + api/db.py get_conn/init_db pattern + api/models.py BaseModel convention + psycopg2 raw SQL pattern

provides:
  - email-validator>=2.0,<3.0 installed and in uv.lock (enables pydantic EmailStr)
  - waitlist table DDL in init_db() (id, email UNIQUE, signed_up_at TIMESTAMPTZ, source)
  - insert_waitlist_email(email) -> str — parameterized INSERT with RETURNING, UniqueViolation -> 409
  - WaitlistRequest(BaseModel) with email: EmailStr field (validated via email-validator)
  - send_waitlist_notification(email, signed_up_at) -> None — smtplib STARTTLS to info@k-innovative.com
  - 5 SMTP env vars documented in .env.example (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM)

affects:
  - 06-02-waitlist-endpoint (consumes all public interfaces created here)
  - future-phases-smtp (reuse send_waitlist_notification pattern for other notifications)

tech-stack:
  added:
    - email-validator==2.3.0 (via uv add "email-validator>=2.0,<3.0")
    - dnspython==2.8.0 (transitive dep of email-validator)
  patterns:
    - UniqueViolation caught outside `with conn:` block (Pitfall 1 avoidance — ensures rollback completes before except runs)
    - RETURNING clause for DB-generated timestamps (avoids Python-side datetime drift)
    - smtplib STARTTLS flow: SMTP(host, port) -> starttls() -> login() -> sendmail()
    - os.environ["KEY"] bracket access for required SMTP vars (KeyError surfaces misconfiguration)
    - No try/except in SMTP helper — exceptions propagate to caller for 500 mapping (D-06)

key-files:
  created:
    - api/email_utils.py (41 lines — send_waitlist_notification SMTP helper)
  modified:
    - pyproject.toml (+1 dependency line — email-validator>=2.0,<3.0)
    - uv.lock (+email-validator==2.3.0, +dnspython==2.8.0)
    - .env.example (+5 SMTP var lines)
    - api/db.py (+31 lines — 2 new imports, waitlist DDL in init_db, insert_waitlist_email function)
    - api/models.py (+4 lines — EmailStr added to import, WaitlistRequest class)

key-decisions:
  - "D-01: stdlib smtplib only — no external email SDK dependency"
  - "D-02: All 5 SMTP vars in .env.example; SMTP_FROM separate from SMTP_USER for shared-mailbox scenario"
  - "D-03: STARTTLS on port 587 (not SMTP_SSL/465) — covers Gmail, Zoho, Mailgun relay"
  - "D-04: Notification recipient hardcoded to info@k-innovative.com — not read from env"
  - "D-06: SMTP failure raises (no try/except in helper) — caller maps to 500 for fail-loudly behavior"
  - "D-07: UNIQUE constraint on email; duplicate -> HTTPException(409, You're already on the waitlist.)"
  - "D-08: Pydantic EmailStr validates RFC-compliant format before any DB or SMTP call"
  - "D-09: waitlist schema: id SERIAL PK, email TEXT NOT NULL UNIQUE, signed_up_at TIMESTAMPTZ DEFAULT NOW(), source TEXT DEFAULT landing_page"
  - "D-10: source hardcoded to landing_page in insert_waitlist_email params"
  - "Pitfall 1: except psycopg2.errors.UniqueViolation placed outside with conn: block so context manager completes rollback first"

patterns-established:
  - "Pattern: UniqueViolation -> 409 via except outside with conn: block (prevents InFailedSqlTransaction)"
  - "Pattern: RETURNING signed_up_at -> cur.fetchone()[0].isoformat() for DB-generated timestamps"
  - "Pattern: smtplib STARTTLS — with smtplib.SMTP(host, port) as smtp: smtp.starttls(); smtp.login(); smtp.sendmail()"
  - "Pattern: required env vars via os.environ[KEY], optional with default via os.environ.get(KEY, default)"

requirements-completed:
  - WAIT-02
  - WAIT-03

duration: 2min
completed: "2026-06-01"
---

# Phase 6 Plan 01: Waitlist Backend Foundation Summary

**Waitlist Postgres table DDL, psycopg2 insert with UniqueViolation-to-409 mapping, Pydantic EmailStr request model, and smtplib STARTTLS owner-notification helper — all primitives Plan 02 needs to wire the public endpoint**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-01T08:06:44Z
- **Completed:** 2026-06-01T08:08:51Z
- **Tasks:** 3
- **Files modified:** 5 (+ 1 created)

## Accomplishments
- Installed email-validator==2.3.0 via uv, updating both pyproject.toml and uv.lock, enabling pydantic EmailStr at import time
- Extended api/db.py with waitlist table DDL in init_db() and insert_waitlist_email() using parameterized SQL with RETURNING clause and UniqueViolation -> HTTPException(409) mapping outside the with conn: block
- Added WaitlistRequest(BaseModel) with email: EmailStr to api/models.py and created api/email_utils.py with send_waitlist_notification() using smtplib STARTTLS on port 587 to info@k-innovative.com

## Public Interfaces Created

### insert_waitlist_email
```python
def insert_waitlist_email(email: str) -> str:
    """Insert email into waitlist. Returns signed_up_at as ISO string.
    Raises HTTPException(409) on duplicate email (D-07)."""
```
- SQL: `INSERT INTO waitlist (email, source) VALUES (%s, %s) RETURNING signed_up_at`
- Returns: `row[0].isoformat()` (DB-generated TIMESTAMPTZ as ISO string)
- Raises: `HTTPException(status_code=409, detail="You're already on the waitlist.")`

### WaitlistRequest
```python
class WaitlistRequest(BaseModel):
    email: EmailStr
```
- `WaitlistRequest(email="ok@example.com")` — succeeds
- `WaitlistRequest(email="garbage")` — raises `pydantic.ValidationError`

### send_waitlist_notification
```python
def send_waitlist_notification(email: str, signed_up_at: str) -> None:
    """Send SMTP owner notification. Raises SMTPException on failure (D-06)."""
```
- Reads: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` from `os.environ["KEY"]`
- Reads: `SMTP_PORT` from `os.environ.get("SMTP_PORT", "587")`
- Hardcoded To: `info@k-innovative.com`
- Flow: `smtplib.SMTP(host, port)` -> `.starttls()` -> `.login()` -> `.sendmail()`
- No try/except — propagates to caller (D-06)

## Decisions Honored

| Decision | One-line Attribution |
|----------|---------------------|
| D-01 | `api/email_utils.py` uses stdlib `smtplib` only — no sendgrid, boto3, or mailjet |
| D-02 | `.env.example` has all 5 SMTP vars; `SMTP_FROM` is separate from `SMTP_USER` |
| D-03 | `smtplib.SMTP(host, port)` + `.starttls()` — no SMTP_SSL branch anywhere |
| D-04 | `to_addr = "info@k-innovative.com"` hardcoded in `send_waitlist_notification`, not read from env |
| D-07 | `UNIQUE` constraint on `email` in DDL; `except UniqueViolation` -> `HTTPException(409)` with exact detail string |
| D-08 | `email: EmailStr` in `WaitlistRequest`; `WaitlistRequest(email="garbage")` raises `ValidationError` |
| D-09 | waitlist DDL: `id SERIAL PK`, `email TEXT NOT NULL UNIQUE`, `signed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `source TEXT NOT NULL DEFAULT 'landing_page'` |
| D-10 | `insert_waitlist_email` hardcodes `"landing_page"` as source param — no dynamic source |

## Task Commits

1. **Task 1: Add email-validator dependency and SMTP env-var template** - `e1a8529` (feat)
2. **Task 2: Extend api/db.py with waitlist table DDL and insert_waitlist_email()** - `40e9905` (feat)
3. **Task 3: Add WaitlistRequest model and api/email_utils.py** - `95bc70f` (feat)

## Files Created/Modified

| File | Change | Lines Added |
|------|--------|-------------|
| `api/email_utils.py` | Created — SMTP notification helper | +41 |
| `api/db.py` | Extended — 2 imports, waitlist DDL, insert_waitlist_email() | +31 |
| `api/models.py` | Extended — EmailStr import, WaitlistRequest class | +4 |
| `pyproject.toml` | Extended — email-validator dependency line | +1 |
| `uv.lock` | Updated — email-validator==2.3.0, dnspython==2.8.0 | auto |
| `.env.example` | Extended — 5 SMTP var placeholder lines | +5 |

## Deviations from Plan

None - plan executed exactly as written. All pitfalls identified in RESEARCH.md were avoided:
- Pitfall 1 (UniqueViolation inside with conn:) — except clause placed at outer try level
- Pitfall 2 (email-validator missing) — installed via uv add before any model changes
- Pitfall 3 (silent SMTP misconfiguration) — bracket access os.environ["KEY"] raises KeyError immediately

## Issues Encountered

None - all acceptance criteria passed on first run.

## User Setup Required

SMTP credentials are required for `send_waitlist_notification` to function. Add to `.env`:

```
SMTP_HOST=<your-smtp-host>
SMTP_PORT=587
SMTP_USER=<your-smtp-username>
SMTP_PASS=<your-smtp-password>
SMTP_FROM=<your-from-address>
```

The `.env.example` file now documents all five vars with placeholder values. The real `.env` is gitignored. Without these vars, the first waitlist signup will return a 500 with `KeyError: 'SMTP_HOST'` — intentional per D-06.

## Outstanding Work for Plan 02

Plan 02 (`06-02`) must complete the following to wire this foundation into a live endpoint:

1. **CORSMiddleware** — add `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])` to `api/main.py` immediately after `app = FastAPI(...)` (D-11)
2. **POST /api/waitlist endpoint** — add `waitlist_signup(body: WaitlistRequest)` handler in `api/main.py` that calls `insert_waitlist_email(body.email)` then `send_waitlist_notification(body.email, signed_up_at)` with SMTP failure mapped to HTTPException(500) (D-05, D-06, D-12)
3. **4 contract tests** in `tests/test_api.py`:
   - `test_waitlist_valid_email_returns_200` — mocks insert + smtp, asserts 200 + response body
   - `test_waitlist_invalid_email_returns_422` — no mocks needed, asserts 422 (Pydantic rejects before handler)
   - `test_waitlist_duplicate_email_returns_409` — mock insert raises HTTPException(409), asserts 409 + detail
   - `test_waitlist_smtp_failure_returns_500` — mock smtp raises Exception, asserts 500
4. **Patch bindings**: tests must patch `api.main.insert_waitlist_email` and `api.main.send_waitlist_notification` (not `api.db.*` or `api.email_utils.*`) — `from ... import` creates local bindings (Pitfall 5 in RESEARCH.md)

## Known Stubs

None — no UI rendering or stub data. All interfaces created are either fully implemented (db function, model, smtp helper) or deferred to Plan 02 (endpoint wiring, tests).

## Threat Flags

All threat mitigations in plan threat model are present in source:

| Threat | Mitigation Verified |
|--------|---------------------|
| T-06-01 Email injection | `email: EmailStr` in WaitlistRequest rejects `\r\n` via RFC-compliant parsing |
| T-06-02 SQL injection | `INSERT ... VALUES (%s, %s)` parameterized — no f-string interpolation |
| T-06-03 SMTP credential leak | All 5 SMTP vars via `os.environ["KEY"]` — no hardcoded secrets in source |
| T-06-04 Duplicate row explosion | `email TEXT NOT NULL UNIQUE` in DDL blocks duplicates at DB layer |
| T-06-05 Connection leak after UniqueViolation | `finally: conn.close()` + UniqueViolation caught outside `with conn:` |
| T-06-06 SMTP header injection | EmailStr already rejects `\r\n` before reaching email_utils |
| T-06-07 Silent SMTP misconfiguration | `os.environ["SMTP_HOST"]` raises KeyError immediately on first call |

No new threat surface beyond what is in the plan's threat model.

---
*Phase: 06-waitlist-backend*
*Completed: 2026-06-01*
