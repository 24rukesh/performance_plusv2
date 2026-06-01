---
phase: 7
slug: landing-page-ui-polish
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-01
---

# Phase 7 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Pydantic-validated LLM output → Streamlit HTML render | `result.campaigns[i].semantic_reasoning` is a gpt-4o Structured Output (Pydantic-validated by `CampaignAction` in `llm.py`) rendered via `st.write()` (auto-escapes). Badge HTML is built from a Pydantic `Literal` enum. No user-supplied input flows into any `unsafe_allow_html` body. | LLM text (untrusted in theory; schema-constrained in practice) |
| Streamlit branded header HTML constant → browser DOM | `BRANDED_HEADER_HTML` is a static string literal defined in source; no interpolation of any external input. | Static string (no user data) |
| npm registry → landing/node_modules | Third-party packages (`next`, `tailwindcss`, `@heroicons/react`, transitive deps) downloaded at install time via `package-lock.json`. | Build-time artifact (no runtime user data) |
| Build-time env (`NEXT_PUBLIC_*`) → JS bundle | `NEXT_PUBLIC_API_BASE_URL` is inlined at build time; falls back to `""` (same-origin) when unset in production. Only non-secret public URLs may use this prefix. | URL string (non-sensitive) |
| Browser visitor email input → WaitlistForm → fetch → FastAPI EmailStr | Untrusted user input validated at browser (`type="email"`) and server (Pydantic `EmailStr` — Phase 6 T-06-01). | PII: email address |
| Same-origin / cross-origin fetch → FastAPI POST /api/waitlist | Local dev: `localhost:3000` → `localhost:8000`. Production: same-origin `/api/waitlist` via Caddy. | Email address (POST body) |
| External link `<a href="/app" target="_blank">` → Streamlit tab | Browser opens a new window. `rel="noopener noreferrer"` prevents `window.opener` access. | Navigation (no data) |
| `next/font/google` build-time fetch → Google CDN → self-hosted woff2 | Fonts downloaded at `npm run build`, then self-hosted in build output. No runtime CDN dependency, no PII transmitted. | Font binary (build time only) |

---

## Threat Register

### Mitigate Threats — Verification Results

| Threat ID | Category | Component | Status | Evidence |
|-----------|----------|-----------|--------|----------|
| T-07-02 | Tampering / XSS | `st.markdown(_badge_html + _pct_html, unsafe_allow_html=True)` in `app.py` | CLOSED | `app.py:10` — `_badge_html, _pct_html` imported from `ui_helpers`. `app.py:173-174` — both helpers called inside `unsafe_allow_html=True` markdown; `_badge_html` accepts only the `budget_action` Pydantic `Literal["increase","pause","decrease","insufficient_data"]`, `_pct_html` accepts `int` only. Neither function echoes user-controlled input. |
| T-07-03 | Tampering / XSS (semantic_reasoning) | `st.write(c.semantic_reasoning)` in `app.py` | CLOSED | `app.py:176` — `st.write(c.semantic_reasoning)` is NOT wrapped in `unsafe_allow_html=True`. `st.write()` auto-escapes HTML/markdown. Even if gpt-4o emitted an HTML payload, it renders as escaped text. |
| T-07-05 | Information Disclosure (env baking) | `NEXT_PUBLIC_API_BASE_URL` in `landing/.env.example` | CLOSED | `landing/.env.example:4` — value is `http://localhost:8000` (non-secret local URL). `landing/components/WaitlistForm.tsx:15` — `const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? ""` falls back to `""` (same-origin) when unset, so production build does NOT bake any URL into the bundle. No secrets under `NEXT_PUBLIC_` prefix. |
| T-07-07 | Information Disclosure (gitignored .env.local) | `landing/.env.local` | CLOSED | `landing/.gitignore:34-35` — `.env*` is ignored, `.env.example` is explicitly unignored (`!.env.example`). Local-dev value (`http://localhost:8000`) is not sensitive even if leaked. |
| T-07-08 | Tampering (Tailwind config drift) | Absence of `landing/tailwind.config.ts` | CLOSED | File does not exist (verified: `ls landing/tailwind.config.ts` → not found). All design tokens live in `@theme` block in `globals.css`. No silent source-of-truth split. |
| T-07-10 | Input Validation (malformed email) | `WaitlistForm` fetch payload `{ email }` | CLOSED | `landing/components/WaitlistForm.tsx:45` — `type="email" required` on the input rejects malformed before submit (browser layer). Server layer: FastAPI `WaitlistRequest` model uses Pydantic `EmailStr` (Phase 6 T-06-01), returns 422 on invalid input before any DB/SMTP call. |
| T-07-11 | Information Disclosure (API error detail) | `WaitlistForm` error branch | CLOSED | `landing/components/WaitlistForm.tsx:22-26` — status mapped to enum literals `"success"` / `"duplicate"` / `"error"` only. `res.json()` is never called; raw server `detail` is never parsed or rendered. Generic hardcoded messages shown to visitors. |
| T-07-12 | Tab-nabbing (target=_blank) | `<a href="/app" target="_blank">` Try Demo CTA | CLOSED | `landing/components/HeroSection.tsx:27-28` — `target="_blank"` accompanied by `rel="noopener noreferrer"`. Prevents `window.opener` access from the newly opened tab. |
| T-07-14 | Hydration mismatch | `WaitlistForm` `useState` initial value | CLOSED | `landing/components/WaitlistForm.tsx:9` — `useState<Status>("idle")` — static literal, no `window` access, no `process.env.*` read during render. `process.env.NEXT_PUBLIC_API_BASE_URL` read at `tsx:15` is inside `handleSubmit`, not in render path. Server and client produce identical initial output. |
| T-07-17 | Tampering (animation timing manipulation) | `IntersectionObserver` disconnect in `DemoAnimation.tsx` | CLOSED | `landing/components/DemoAnimation.tsx:67` — `observer.disconnect()` called on first `isIntersecting: true`. Animation cannot be re-triggered via DOM manipulation. `animation-fill-mode: both` holds final state. |
| T-07-18 | Denial of Service (animation memory leak) | `useEffect` cleanup in `DemoAnimation.tsx` | CLOSED | `landing/components/DemoAnimation.tsx:73` — `return () => observer.disconnect()` as `useEffect` cleanup. Observer is also self-disconnected on first intersection (T-07-17). No leaked observer if component unmounts during scroll. |

### Accepted Risk Threats

| Threat ID | Category | Status | Accepted Risk Rationale |
|-----------|----------|--------|------------------------|
| T-07-01 | Tampering / XSS | CLOSED/accepted | `BRANDED_HEADER_HTML` is a hardcoded module-level constant in `app.py` (lines 14+) with zero string interpolation. No user input touches this path. Risk is structurally absent. |
| T-07-04 | Information Disclosure (link href) | CLOSED/accepted | `<a href="/" target="_self">` in branded header is a hardcoded relative path. No sensitive query strings, no user data in URL. In production Caddy (Phase 8) routes `/` to Next.js landing page. |
| T-07-06 | Tampering (supply chain — npm) | CLOSED/accepted | All four primary deps (`next`, `tailwindcss`, `react`, `@heroicons/react`) are top-N npm packages with active maintainers. `package-lock.json` committed for reproducible installs. Default `registry.npmjs.org` only. Risk is equivalent to any Node.js project; standard for v2.0. |
| T-07-09 | Tampering (XSS via React) | CLOSED/accepted | All strings in `HeroSection`, `HowItWorksSection`, `WaitlistForm` are JSX text children; React auto-escapes these. No `dangerouslySetInnerHTML` found in any landing component (verified: grep returned no results). |
| T-07-13 | CSRF on /api/waitlist | CLOSED/accepted | Endpoint is public, idempotent on user intent (waitlist signup), returns 409 on duplicate (no destructive side effect). CORS wildcard accepted per Phase 6 D-05 / T-06-09. No cookies or credentials transmitted. CSRF token deferred per `06-CONTEXT.md §Deferred`; revisit when auth is added. |
| T-07-15 | Tampering (XSS via React — demo cards / footer) | CLOSED/accepted | All 4 demo card strings and footer copy are source literals rendered as JSX text. React auto-escapes. No `dangerouslySetInnerHTML` in any file (build-time TypeScript + grep gate confirmed). Inline style props on demo card badges set CSS only (no `__html`). |
| T-07-16 | Information Disclosure (font CDN fetch at build) | CLOSED/accepted | `next/font/google` downloads woff2 files from Google at `npm run build`; fonts then self-hosted in build output with no runtime CDN dependency. No PII transmitted. Standard Next.js behavior. |
| T-07-19 | Supply chain (Heroicons import) | CLOSED/accepted | `@heroicons/react` maintained by Tailwind Labs (MIT). Tree-shaken at build — only the 4 imported icon symbols ship in the bundle. UI-SPEC permits inline SVG fallback if the dep is later removed. |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-07-01 | T-07-01 | Static hardcoded constant — no attack surface exists | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-02 | T-07-04 | Hardcoded relative path — no data leakage | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-03 | T-07-06 | Standard npm ecosystem supply chain — package-lock.json committed | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-04 | T-07-09 | React auto-escapes JSX text — no dangerouslySetInnerHTML | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-05 | T-07-13 | Public idempotent endpoint, no auth required at v2.0 stage; defer CSRF token to auth phase | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-06 | T-07-15 | Source-literal JSX strings, React auto-escapes — no dangerouslySetInnerHTML | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-07 | T-07-16 | Standard Next.js self-hosted font pattern — no runtime CDN dependency | plan-time (PLAN.md) | 2026-06-01 |
| AR-07-08 | T-07-19 | MIT Tailwind Labs package — tree-shaken, inline SVG fallback available | plan-time (PLAN.md) | 2026-06-01 |

---

## Unregistered Threat Flags

**07-01-SUMMARY.md through 07-04-SUMMARY.md:** No `## Threat Flags` sections present. No unregistered attack surface flagged by the executor.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-01 | 19 | 19 | 0 | gsd-secure-phase (automated) |

---

## Summary

**Threats closed:** 19/19 (11 mitigate + 8 accept)
**Threats open:** 0
**Blockers:** none
**Unregistered flags:** none

All declared mitigations for Phase 7 are present in the implementation files at the locations verified above. The phase is clear to advance.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-01
