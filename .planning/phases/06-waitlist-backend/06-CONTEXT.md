# Phase 6: Waitlist Backend - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `POST /api/waitlist` endpoint to the existing FastAPI service that accepts a visitor's email address, stores it in a new `waitlist` Postgres table, and sends an SMTP notification to the product owner at info@k-innovative.com. Builds entirely on the Phase 5 FastAPI + Postgres stack — no new services, no new Docker containers.

Phase 6 scope: new endpoint in `api/main.py`, new DB functions in `api/db.py`, new `waitlist` table in `init_db()`, SMTP helper using stdlib `smtplib`, CORS middleware added to FastAPI, env var additions to `.env.example`. No Caddy changes (Phase 8). No UI changes.

</domain>

<decisions>
## Implementation Decisions

### SMTP Email Notification
- **D-01:** Use **stdlib `smtplib`** only — no external email SDK dependency. Generic SMTP with configurable env vars. No hardcoded provider.
- **D-02:** Env vars: `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`. `SMTP_FROM` may differ from `SMTP_USER` (e.g., shared mailbox). All five vars added to `.env.example`.
- **D-03:** Transport: **STARTTLS on port 587** — `smtplib.SMTP(host, port)` + `.starttls()` + `.login()`. Covers Gmail, Zoho, Mailgun relay, and most providers. No `smtplib.SMTP_SSL` branch needed.
- **D-04:** Notification recipient is hardcoded to `info@k-innovative.com` (the product owner address — fixed per project context).

### Email Send Timing
- **D-05:** SMTP notification is sent **inline and synchronously** within the `POST /api/waitlist` handler — DB insert first, then SMTP send, then return 200. No background threads.
- **D-06:** If the SMTP send fails, the endpoint returns **500 with error detail**. Failing loudly ensures SMTP misconfiguration is caught immediately during setup. The owner not being notified violates WAIT-03, so a 200 would be misleading.

### Duplicate Email Handling
- **D-07:** The `waitlist` table has a **UNIQUE constraint on `email`**. Duplicate submissions return **409 Conflict** with the message `"You're already on the waitlist."` No duplicate rows, no duplicate owner notifications.
- **D-08:** Email format validation uses **Pydantic's `EmailStr`** (via `email-validator` package). Invalid email format returns a standard 422 Unprocessable Entity before any DB or SMTP call.

### Postgres Schema
- **D-09:** `waitlist` table schema: `id (SERIAL PK)`, `email (TEXT NOT NULL UNIQUE)`, `signed_up_at (TIMESTAMPTZ NOT NULL DEFAULT NOW())`, `source (TEXT NOT NULL DEFAULT 'landing_page')`. Added to `init_db()` in `api/db.py` alongside existing `analysis_results` and `pending_sessions` tables.
- **D-10:** `source` defaults to `'landing_page'` — hardcoded in the Phase 6 handler. Future phases could pass a different source string.

### CORS
- **D-11:** Add **`CORSMiddleware`** to the FastAPI app in Phase 6. `allow_origins=["*"]` — wildcard is safe for a public, credential-free waitlist endpoint. Covers Phase 7 Next.js local dev calls without a proxy workaround. No new dependency (`fastapi.middleware.cors` is built in).

### Endpoint Access
- **D-12:** `POST /api/waitlist` is a **public endpoint — no `verify_api_key` dependency**. Landing page visitors don't have API keys. All other protected endpoints from Phase 5 remain unchanged.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stack & Existing Service
- `./CLAUDE.md` — Python 3.11, uv, `python:3.11-slim-bookworm`, env var handling. Read "TL;DR" and "What NOT to Use" sections.
- `.planning/PROJECT.md` — Constraints, v2.0 goals. Owner email is info@k-innovative.com (fixed).
- `.planning/ROADMAP.md` — Phase 6 success criteria (3 items that must be TRUE); requirements WAIT-01, WAIT-02, WAIT-03.
- `.planning/REQUIREMENTS.md` §Waitlist — WAIT-01, WAIT-02, WAIT-03 full requirement text.

### Phase 5 Patterns to Extend (not duplicate)
- `.planning/phases/05-fastapi-service/05-CONTEXT.md` — D-09 (psycopg2 raw SQL), D-12 (auth dependency pattern), `get_conn()`, `init_db()`, `verify_api_key` — reuse all of these. `POST /api/waitlist` does NOT use `verify_api_key`.
- `./api/db.py` — `get_conn()`, `init_db()` — extend `init_db()` with the `waitlist` table CREATE. Add `insert_waitlist_email()` and `get_waitlist_entry()` functions using the same psycopg2 pattern.
- `./api/main.py` — Add `POST /api/waitlist` endpoint and `CORSMiddleware`. Do not modify any existing Phase 5 endpoints.
- `./api/models.py` — Add `WaitlistRequest(BaseModel)` with `email: EmailStr` field.

### Dependencies
- `pyproject.toml` — Add `email-validator` (for Pydantic `EmailStr`). No other new packages needed.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/db.get_conn()`: Opens a new psycopg2 connection. All new waitlist DB functions follow the same `conn = get_conn(); try: with conn: ...; finally: conn.close()` pattern.
- `api/db.init_db()`: Creates tables at lifespan startup. Add `waitlist` table CREATE IF NOT EXISTS here alongside the two existing tables.
- `api/main.app`: FastAPI app instance — add `CORSMiddleware` via `app.add_middleware(CORSMiddleware, ...)` after the app is created.
- `api/main.verify_api_key`: Existing dependency — `POST /api/waitlist` intentionally does NOT use it.
- `llm.AnalysisResult` / `api/models.py` pattern: New `WaitlistRequest` model lives in `api/models.py` with `email: EmailStr`.

### Established Patterns
- psycopg2 raw parameterized SQL — no ORM, no f-strings in SQL.
- `DATABASE_URL` env var via `os.environ["DATABASE_URL"]` (raises `KeyError` if unset — intentional, surfaces misconfiguration).
- `uv run` for all shell invocations.
- Env vars via `.env` file + `python-dotenv` in local dev, `compose.yaml` `env_file:` in Docker.

### Integration Points
- Modified files: `api/main.py` (new endpoint + CORS middleware), `api/db.py` (waitlist table + functions), `api/models.py` (WaitlistRequest model), `pyproject.toml` (add `email-validator`), `.env.example` (5 new SMTP vars)
- New module: `api/email_utils.py` (or inline SMTP helper in `api/main.py`) — SMTP send logic using `smtplib`
- The `waitlist` table is in the same Postgres DB as `analysis_results` and `pending_sessions` — same `DATABASE_URL`, no schema separation

</code_context>

<specifics>
## Specific Ideas

- Response body for 200: `{ "message": "You're on the waitlist! We'll be in touch." }` — simple acknowledgement matching WAIT-01.
- Response body for 409: `{ "detail": "You're already on the waitlist." }` — FastAPI HTTPException style.
- Owner notification email subject: `"New waitlist signup: {email}"` — contains the email in subject for quick scanning in inbox.
- Owner notification email body (plain text): `"New signup on Performance Plus waitlist.\n\nEmail: {email}\nTimestamp: {signed_up_at}\nSource: landing_page"`.
- SMTP helper should be extractable to `api/email_utils.py` with a single function `send_waitlist_notification(email: str, signed_up_at: datetime) -> None` — keeps `main.py` clean.

</specifics>

<deferred>
## Deferred Ideas

- **Welcome email to the visitor** — Sending a confirmation email to the person who signed up (not just the owner). Nice-to-have but not in WAIT-03. Future phase.
- **Waitlist management endpoint** — `GET /api/waitlist` to list all signups (owner-only, protected). Useful for SaaS operations. Future phase.
- **Rate limiting on /api/waitlist** — Prevent spam signups. Single-tenant demo doesn't need it yet.
- **ALLOWED_ORIGINS env var** — Restrict CORS to specific domains in production. Wildcard is fine for MVP; lockdown is a future hardening task.

</deferred>

---

*Phase: 6-Waitlist Backend*
*Context gathered: 2026-06-01*
