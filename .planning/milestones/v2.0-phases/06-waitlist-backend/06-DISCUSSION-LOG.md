# Phase 6: Waitlist Backend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-01
**Phase:** 6-waitlist-backend
**Areas discussed:** SMTP provider, Email send timing, Duplicate email handling, CORS for Phase 7

---

## SMTP Provider

| Option | Description | Selected |
|--------|-------------|----------|
| Generic SMTP env vars | SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM in .env.example. Works with Gmail, Zoho, Mailgun relay, any provider. stdlib smtplib only. | ✓ |
| Gmail SMTP hardcoded | Hardcode smtp.gmail.com:587 in code, only SMTP_USER + SMTP_PASS needed. Simpler config but locked to Gmail App Password. | |
| SendGrid API | sendgrid Python SDK, SENDGRID_API_KEY in .env. 100 free emails/day. Adds a new dependency. | |

**User's choice:** Generic SMTP env vars (recommended)
**Notes:** Chose SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM (5 vars) — SMTP_FROM kept separate to support shared mailboxes. STARTTLS port 587 selected for transport.

---

## Email Send Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Inline sync | DB insert + SMTP send before returning 200. Simple code, errors are visible. | ✓ |
| Background thread | threading.Thread(target=send_email).start() after DB insert. Response returns immediately but email errors are silent. | |
| You decide | Claude picks based on phase goals. | |

**User's choice:** Inline sync (recommended)
**Notes:** SMTP failure → 500 with error detail. Failing loudly was chosen over silent 200 because the owner not being notified violates WAIT-03's intent. Errors surface misconfiguration immediately during setup.

---

## Duplicate Email Handling

| Option | Description | Selected |
|--------|-------------|----------|
| 409 Conflict with message | UNIQUE constraint on email. Second submission returns 409 + "You're already on the waitlist." No duplicate rows or notifications. | ✓ |
| Silent 200 success | UNIQUE constraint + INSERT OR IGNORE. Same confirmation message. No 409 exposed. | |
| Allow duplicates | No unique constraint. Every submission inserts a new row and sends a new owner notification. | |

**User's choice:** 409 Conflict (recommended)
**Notes:** Schema: id (SERIAL PK), email (TEXT NOT NULL UNIQUE), signed_up_at (TIMESTAMPTZ DEFAULT NOW()), source (TEXT NOT NULL DEFAULT 'landing_page'). Pydantic EmailStr chosen for email format validation.

---

## CORS for Phase 7

| Option | Description | Selected |
|--------|-------------|----------|
| Add CORS middleware in Phase 6 | CORSMiddleware, allow_origins=["*"]. Zero new dependency. Phase 7 Next.js local dev works immediately. | ✓ |
| Defer to Phase 8 (Caddy) | In production, same-domain routing eliminates CORS. Local dev needs a workaround. | |

**User's choice:** Yes, add CORS middleware in Phase 6 (recommended)
**Notes:** allow_origins=["*"] chosen — safe for public, credential-free waitlist endpoint. Wildcard avoids Phase 7 config coordination.

---

## Claude's Discretion

None — all four areas had clear user choices. The following were filled in by Claude with reasonable defaults and noted in specifics:
- Email subject line format: `"New waitlist signup: {email}"`
- Email body format: plain text with email, timestamp, and source
- SMTP helper extracted to `api/email_utils.py`
- 200 response body: `{ "message": "You're on the waitlist! We'll be in touch." }`

---

## Deferred Ideas

- Welcome email to the visitor (not just the owner) — future phase
- `GET /api/waitlist` management endpoint (owner-only) — future phase
- Rate limiting on `/api/waitlist` to prevent spam — future phase
- `ALLOWED_ORIGINS` env var for CORS lockdown in production — future hardening
