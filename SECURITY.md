# SECURITY.md — Phase 6: Waitlist Backend

**Phase:** 6 — Waitlist Backend
**Plans audited:** 06-01 (Foundation), 06-02 (Endpoint + Tests)
**ASVS Level:** 1
**Audit date:** 2026-06-01
**Auditor:** gsd-secure-phase (automated)

---

## Threat Verification

### Mitigate Threats — Verification Results

| Threat ID | Category | Component | Status | Evidence |
|-----------|----------|-----------|--------|----------|
| T-06-01 | Tampering | api/models.py WaitlistRequest | CLOSED | `api/models.py:1` — `from pydantic import BaseModel, EmailStr`; `api/models.py:35` — `email: EmailStr`. EmailStr rejects addresses containing `\r\n` and malformed format before any DB or SMTP call. |
| T-06-02 | Tampering | api/db.py insert_waitlist_email | CLOSED | `api/db.py:126` — `"INSERT INTO waitlist (email, source) VALUES (%s, %s) RETURNING signed_up_at"` with params tuple `(email, "landing_page")` at line 127. No f-string interpolation present in the SQL statement. |
| T-06-03 | Information Disclosure | SMTP credentials | CLOSED | `api/email_utils.py:18,20,21,22` — all four required SMTP vars loaded via `os.environ["KEY"]` bracket access (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`). `SMTP_PORT` uses `os.environ.get("SMTP_PORT", "587")` with safe default. No hardcoded credential strings found in source. |
| T-06-04 | Denial of Service | Postgres waitlist table | CLOSED | `api/db.py:44` — `email        TEXT NOT NULL UNIQUE` in the `CREATE TABLE IF NOT EXISTS waitlist` DDL inside `init_db()`. UNIQUE constraint enforced at DB layer. |
| T-06-05 | Denial of Service | insert_waitlist_email connection leak | CLOSED | `api/db.py:131,133-134` — `except psycopg2.errors.UniqueViolation:` is at 4-space indent (same level as `try:` at line 122), outside the `with conn:` block at line 123 (8-space indent). `finally: conn.close()` at line 133-134 wraps both success and failure paths. Context manager completes rollback before except runs. |
| T-06-06 | Tampering | api/email_utils.py SMTP envelope | CLOSED | `api/email_utils.py:22` — `from_addr = os.environ["SMTP_FROM"]` (operator-controlled env var, not user input). `email` value interpolated into Subject and body (`api/email_utils.py:25,28`) only after EmailStr validation (T-06-01) has already rejected any `\r\n`-containing input. `signed_up_at` is DB-generated (`row[0].isoformat()` at `api/db.py:130`), not user-supplied. |
| T-06-07 | Repudiation | Missing SMTP env var | CLOSED | `api/email_utils.py:18` — `host = os.environ["SMTP_HOST"]` uses bracket access. Missing env var raises `KeyError` immediately on first call, propagates as 500 per D-06. No `os.environ.get(...)` silent fallback for required vars. |
| T-06-10 | Tampering | POST /api/waitlist email-header injection | CLOSED | `api/main.py:77` — `def waitlist_signup(body: WaitlistRequest):`. FastAPI runs Pydantic model validation on `WaitlistRequest` (which carries `email: EmailStr`) before the handler body at lines 78-83 executes. 422 is returned for invalid input without reaching DB or SMTP. |
| T-06-13 | Tampering | tests/test_api.py monkeypatch binding | CLOSED | `tests/test_api.py:82-83` — `_make_client` factory applies `monkeypatch.setattr(f"api.main.{name}", mock)` for each entry in `db_overrides`. Waitlist tests at lines 416-418, 438, 448-450 pass `"insert_waitlist_email"` and `"send_waitlist_notification"` as keys — both resolve to `api.main.insert_waitlist_email` and `api.main.send_waitlist_notification` respectively, matching the `from ... import` bindings at `api/main.py:11-12`. No direct patching of `api.db.*` or `api.email_utils.*` found in waitlist tests. |
| T-06-14 | Repudiation | DB/SMTP call order in waitlist_signup | CLOSED | `api/main.py:78` — `signed_up_at = insert_waitlist_email(body.email)` executes first; the `with conn:` context manager in `insert_waitlist_email` commits before returning (`api/db.py:123,130`). Only after the return does line 80 call `send_waitlist_notification(body.email, signed_up_at)`. DB commit is guaranteed before any SMTP attempt. |
| T-06-15 | Tampering | POST /api/waitlist auth regression | CLOSED | `api/main.py:77` — `def waitlist_signup(body: WaitlistRequest):` has exactly one parameter. No `Depends(verify_api_key)` present. `tests/test_api.py:420` — `client.post("/api/waitlist", json={"email": "user@example.com"})` posts without `headers={"X-API-Key": ...}` and asserts `status_code == 200`. Any future addition of `Depends(verify_api_key)` will break this test. |

### Accepted Risk Threats

| Threat ID | Category | Status | Accepted Risk Rationale |
|-----------|----------|--------|------------------------|
| T-06-08 | Information Disclosure | CLOSED/accepted | D-06 explicit choice: SMTP failure detail (`f"SMTP error: {exc}"`) surfaces in 500 response. Single-tenant MVP with owner-only deployment; no public PII exposure risk. Multi-tenant hardening (scrub `{exc}` repr) deferred per plan decision log. |
| T-06-09 | Spoofing | CLOSED/accepted | D-12 explicit choice: endpoint is public — landing-page visitors do not have API keys. CORS wildcard (`allow_origins=["*"]`) accepted for credential-free signup flow. No cookies or credentials are transmitted. Future hardening (ALLOWED_ORIGINS env var, hCaptcha) deferred per 06-CONTEXT.md §Deferred. |
| T-06-11 | Information Disclosure | CLOSED/accepted | Same rationale as T-06-08 — SMTP failure detail in 500 response accepted per D-06 for single-tenant MVP. |
| T-06-12 | Denial of Service | CLOSED/accepted | UNIQUE constraint (T-06-04) blocks per-email row growth. Distinct-email flood is possible but rate limiting is explicitly deferred per 06-CONTEXT.md §Deferred. Caddy edge rate limiting is available for Phase 8 addition. |

---

## Unregistered Threat Flags

**06-01-SUMMARY.md `## Threat Flags` section:** All seven mitigations listed map directly to registered threats T-06-01 through T-06-07. No unregistered attack surface flagged.

**06-02-SUMMARY.md:** No `## Threat Flags` section present. No unregistered attack surface flagged by the executor.

---

## Summary

**Threats closed:** 11/11 (7 mitigate + 4 accept)
**Threats open:** 0
**Blockers:** none
**Unregistered flags:** none

All declared mitigations for Phase 6 are present in the implementation files at the exact locations and with the exact patterns specified in the threat register. The phase is clear to ship.
