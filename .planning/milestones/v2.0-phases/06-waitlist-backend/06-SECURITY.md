---
phase: 6
slug: waitlist-backend
status: verified
threats_open: 0
asvs_level: 1
created: "2026-06-01"
---

# Phase 6 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| HTTP client → FastAPI request body | Visitor-supplied email arrives as untrusted JSON before validation | email string (PII) |
| FastAPI process → Postgres | Email value crosses into a SQL statement via parameterized binding | email string |
| FastAPI process → SMTP relay | Email + DB-generated timestamp cross into an outbound SMTP envelope | email, timestamp |
| Filesystem → process env | SMTP credentials enter the process via env vars | SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_PORT |
| Untrusted browser → public POST /api/waitlist | No API key required; any cross-origin frontend can POST | email string |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-06-01 | Tampering | api/models.py WaitlistRequest | mitigate | `email: EmailStr` field — rejects malformed addresses and `\r\n` (email-header injection) via email-validator before any DB/SMTP call | closed |
| T-06-02 | Tampering | api/db.py insert_waitlist_email | mitigate | `INSERT INTO waitlist (email, source) VALUES (%s, %s)` parameterized — no f-string interpolation; SQL injection impossible | closed |
| T-06-03 | Information Disclosure | SMTP credentials | mitigate | All 5 SMTP vars via `os.environ["KEY"]` bracket access in api/email_utils.py — zero hardcoded credential strings; `.env` gitignored | closed |
| T-06-04 | Denial of Service | Postgres waitlist table | mitigate | `email TEXT NOT NULL UNIQUE` constraint in waitlist DDL blocks duplicate row growth at DB layer | closed |
| T-06-05 | Denial of Service | insert_waitlist_email connection leak | mitigate | `except psycopg2.errors.UniqueViolation` at outer-try level (outside `with conn:`) + `finally: conn.close()` covers all paths | closed |
| T-06-06 | Tampering | api/email_utils.py SMTP envelope | mitigate | `email` already EmailStr-validated (blocks `\r\n`); `from_addr` from `os.environ["SMTP_FROM"]` (operator-controlled); `signed_up_at` DB-generated | closed |
| T-06-07 | Repudiation | Silent SMTP misconfiguration | mitigate | `os.environ["SMTP_HOST"]` bracket access raises `KeyError` immediately on misconfigured deployment | closed |
| T-06-08 | Information Disclosure | SMTP failure detail in 500 response | accept | See Accepted Risks Log — AR-06-01 | closed |
| T-06-09 | Spoofing | POST /api/waitlist — no auth, any origin | accept | See Accepted Risks Log — AR-06-02 | closed |
| T-06-10 | Tampering | Email-header injection via `\r\n` reaching SMTP | mitigate | `body: WaitlistRequest` parameter causes FastAPI to run Pydantic/EmailStr validation before handler body executes | closed |
| T-06-11 | Information Disclosure | SMTP failure detail leaks internal info | accept | See Accepted Risks Log — AR-06-01 (same as T-06-08) | closed |
| T-06-12 | Denial of Service | Unauthenticated signup flood | accept | See Accepted Risks Log — AR-06-03 | closed |
| T-06-13 | Tampering | Test harness patching wrong module binding | mitigate | `_make_client(db_overrides={"insert_waitlist_email": ...})` patches at `api.main.*` binding level — correct import path tested and verified | closed |
| T-06-14 | Repudiation | SMTP sent before DB commit | mitigate | `insert_waitlist_email` called first (returns after `with conn:` commits); `send_waitlist_notification` called only after DB commit | closed |
| T-06-15 | Tampering | Future `Depends(verify_api_key)` regression on public endpoint | mitigate | Handler has exactly one param `body: WaitlistRequest`; `test_waitlist_valid_email_returns_200` posts without X-API-Key and asserts 200 — regression turns test red | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-01 | T-06-08, T-06-11 | D-06 (fail-loudly): `detail=f"SMTP error: {exc}"` in 500 response may reveal SMTP host or auth state. Accepted for single-tenant MVP — owner-only deployment, no public error listing. Harden (scrub exc repr) in multi-tenant release. | gsd-security-auditor | 2026-06-01 |
| AR-06-02 | T-06-09 | D-12: POST /api/waitlist is explicitly public — landing page visitors don't have API keys. CORS wildcard (`allow_origins=["*"]`) accepted for credential-free MVP. Future hardening: ALLOWED_ORIGINS env var, hCaptcha. Rate limiting in Phase 8. | gsd-security-auditor | 2026-06-01 |
| AR-06-03 | T-06-12 | UNIQUE constraint blocks per-email row growth from a single attacker's address. Distinct-email flooding possible; rate limiting explicitly deferred per 06-CONTEXT.md. Caddy edge rate limiting can be added in Phase 8 without code changes. | gsd-security-auditor | 2026-06-01 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-01 | 15 | 15 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log (AR-06-01, AR-06-02, AR-06-03)
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-01
