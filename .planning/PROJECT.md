# Performance Plus — Autonomous Semantic Attribution Engine

## What This Is

A GenAI-native performance marketing tool that stitches web analytics data from multiple ad platforms with CRM sales notes and uses gpt-4o to translate qualitative lead sentiment into immediate, quantitative ad budget decisions. Built as a hackathon MVP (OpenAI x Outskill AI Builders Cohort 01), now evolved into a multi-source analytics platform with a public marketing site, API layer, waitlist backend, and unified VPS deployment.

The app ingests ad platform CSVs (Google Ads, Meta Ads, LinkedIn, custom) and a CRM CSV, normalizes costs to USD via FX_RATES, merges them via `session_id`, and sends unified multi-source data to an OpenAI gpt-4o "autonomous CMO" agent. Results include per-campaign budget action recommendations (increase/pause/decrease by %) with cross-platform comparisons, interactive charts, filters/comparison/drill-down views, PDF/CSV export, and Postgres-backed save/reload. External clients can also call the FastAPI service (POST /api/analyze), and the demo runs offline via fixture fallback when OpenAI is unavailable.

## Core Value

A marketer can load demo data and instantly get AI-reasoned budget routing decisions based on what sales reps actually said about each lead — not just what the click data shows.

## Requirements

### Validated

- ✓ System architecture diagram (Mermaid flowchart) — v1.0-design
- ✓ User flow diagrams showing all key screen transitions — v1.0-design
- ✓ Screen designs (data load, stitched dataframe preview, AI results) — v1.0-design
- ✓ Mock data schema documented (CRM CSV + Web Analytics CSV + session_id join key) — v1.0-design
- ✓ CSV ingest + session_id stitch (pandas inner merge with validate="m:1") — v1.0
- ✓ gpt-4o Structured Outputs (client.beta.chat.completions.parse + Pydantic) — v1.0
- ✓ Streamlit app: demo data load, analysis run, Budget Action Results display — v1.0
- ✓ Docker + Caddy VPS deployment (single-container Streamlit) — v1.0
- ✓ FastAPI service: POST /analyze, POST /webhook/crm, GET /campaigns/{id}/actions, GET /health, API key auth — v2.0 Phase 5
- ✓ Waitlist backend: Postgres table, POST /api/waitlist, SMTP email notification to info@k-innovative.com — v2.0 Phase 6
- ✓ Next.js landing page: hero + waitlist form + How It Works + animated demo cards + features grid + footer — v2.0 Phase 7
- ✓ Streamlit UI polish: branded header (BRANDED_HEADER_HTML), st.expander per-campaign results — v2.0 Phase 7
- ✓ Docker Compose multi-service orchestration: landing + fastapi + app + postgres + caddy — v2.0 Phase 8
- ✓ Caddy multi-route proxy: / → Next.js, /api/* → FastAPI, /app* → Streamlit — v2.0 Phase 8

### Validated (v3.0)

- ✓ Multi-source ad platform CSV upload with per-file currency selection — v3.0 Phase 9
- ✓ Auto-suggest CRM column mapping UI with explicit Confirm Mapping gate — v3.0 Phase 9
- ✓ FX normalization to USD via static FX_RATES (17 currencies) before aggregation — v3.0 Phase 9
- ✓ Cross-platform AI recommendations with `source_platforms` per campaign action — v3.0 Phase 10
- ✓ tiktoken 60k token gate (count_prompt_tokens, o200k_base, st.warning + "Continue anyway") — v3.0 Phase 10
- ✓ 3-tab results layout (Data Preview / Charts / Campaign Actions) with Plotly Express charts — v3.0 Phase 11
- ✓ Filters & Sort, max-3 comparison, session-level drill-down in Campaign Actions tab — v3.0 Phase 11
- ✓ PDF export (fpdf2) + CSV download via st.download_button — v3.0 Phase 11
- ✓ Postgres save/reload analysis (st_db.py, analysis_runs table, JSONB storage) — v3.0 Phase 12
- ✓ OpenAI error fallback to fixture (DEMO_MODE) + api_fallback_active banner — v3.0 Phase 12

### Active

Requirements for the next milestone will be defined via `/gsd:new-milestone`.

### Out of Scope

- Real Meta/Google/LinkedIn Ads API write-back — mock JSON payload only; full API wiring is post-hackathon
- Real CRM/GA data ingestion — synthetic/mock CSV data for the demo
- Full user authentication (login/accounts/sessions) — waitlist-only for now; auth adds 2-3 phases
- Multi-tenant isolation — single-tenant API with API key for current iteration
- Stripe/billing — no paid tier yet (waitlist phase)
- Redis job queue / async background jobs — synchronous API calls sufficient for current scale
- HubSpot/Salesforce direct API pull — generic webhook covers current needs; named CRM integrations are v3+

## Current State

**Version:** v3.0 — Advanced Analytics & Multi-Source (shipped 2026-06-04)

**Live at:** https://agent.rukesh.in  
- `/` — Next.js marketing landing page (hero, How It Works, animated demo, features, waitlist form)  
- `/api/*` — FastAPI service (POST /analyze, POST /webhook/crm, GET /health, etc.)  
- `/app` — Streamlit multi-source analytics app (4-platform upload, CRM mapping, charts, save/reload)

**Stack:** Python 3.11 + Streamlit + FastAPI + Pandas + OpenAI gpt-4o + Postgres + Plotly + fpdf2 + tiktoken + Next.js 16 + Tailwind v4 + Docker Compose + Caddy

**Tests:** 139 passing, 2 pre-existing failures (pytest) · TypeScript clean (tsc --noEmit)

**Codebase:** ~2,446 LOC Python + ~990 LOC TypeScript/TSX

## Constraints

- **Tech Stack:** Python 3.11+, Streamlit, Pandas, OpenAI gpt-4o — fixed for hackathon judging criteria
- **LLM:** OpenAI gpt-4o only (hackathon is OpenAI-sponsored)
- **Data:** Synthetic/mock data only for demo — no real user data handling required
- **Output format:** Strict JSON via `client.beta.chat.completions.parse()` + Pydantic — LLM must return deterministic structured output
- **Deployment:** Self-hosted VPS with Docker — Coolify not in scope

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit over React/Next.js for demo UI | Rapid dashboarding for hackathon timeline; Python-native | ✓ Good — confirmed by design mockups |
| Mock data only (no real Meta API) | Reduces scope to provable AI concept; real integration is post-hackathon | ✓ Good — scope stays manageable |
| gpt-4o as "autonomous CMO" via system prompt | Forces deterministic JSON output; hackathon favors advanced model usage | ✓ Good — Structured Outputs with Pydantic works reliably |
| session_id as join key | Cleanest attribution without a full CDP | ✓ Good — validated in schema design |
| Two milestones: user flow first, then working product | Design validation before building; mirrors hackathon checkpoint structure | ✓ Good — design artifacts shipped on schedule |
| D-03: Badge pill table (not card grid) | Cleaner for tabular campaign data; Streamlit-native | ✓ Good — demonstrated in 03-results.html |
| pd.merge inner join + validate="m:1" | Prevents NaN rows reaching LLM; catches duplicate session_ids early | ✓ Good — documented in schema + mockup |
| psycopg2 raw parameterized SQL (no ORM) | No SQLAlchemy wheel complexity on Python 3.11-slim; sync matches FastAPI sync def | ✓ Good — 14 API tests pass without live Postgres |
| smtplib stdlib for SMTP (no sendgrid/mailjet) | Zero external email SDK dependency; STARTTLS covers major relays | ✓ Good — works with Gmail, Zoho, Mailgun |
| Tailwind v4 CSS-first @theme block | v4 silently ignores tailwind.config.ts; CSS-first is the correct v4 pattern | ✓ Good — design tokens propagate cleanly |
| NEXT_PUBLIC_API_BASE_URL absent in production | Same-origin /api path via Caddy; env var only for local dev | ✓ Good — no build-time URL baking |
| Island architecture (Server + Client islands) | Next.js Server Components for static sections; minimal client boundary | ✓ Good — production build clean, tsc clean |
| handle vs handle_path in Caddyfile | handle preserves /api/ prefix (FastAPI needs it); handle_path strips /app prefix (Streamlit serves at /) | ✓ Good — 7 deploy config tests pass |
| Postgres pg_isready healthcheck + service_healthy condition | Eliminates FastAPI init_db() startup race on cold compose up | ✓ Good — no connection errors at cold start |
| .env* glob in landing/.dockerignore | Prevents .env.local NEXT_PUBLIC_ value from baking into production JS bundle | ✓ Good — production URL is clean relative path |
| cost_usd column name kept for reporting currency | Preserves compute_campaign_agg compatibility without touching data.py when FX normalization added | ✓ Good — zero data.py breaking changes in Phase 9 |
| difflib.get_close_matches over rapidfuzz for CRM mapping | No additional dependency for 4-field matching | ✓ Good — stdlib solution sufficient |
| Source-prefix applied BEFORE pd.concat (not after) | Prevents column name ambiguity when same column exists in multiple platforms | ✓ Good — collision guard catches any violations |
| SLUG_TO_DISPLAY constant instead of .title() | .title() produces "Linkedin Ads" (wrong); constant ensures "LinkedIn Ads" | ✓ Good — display names correct across all surfaces |
| o200k_base tiktoken encoding (not cl100k_base) | gpt-4o-2024-08-06 uses o200k_base; cl100k_base undercounts tokens | ✓ Good — token gate accurate |
| chart_df built outside st.tabs() | Avoids expensive recompute on every tab switch (Streamlit re-runs full script on tab change) | ✓ Good — charts load without re-running aggregation |
| bytes(pdf.output()) wrapping for fpdf2 | st.download_button requires bytes; fpdf2 returns bytearray without wrapping | ✓ Good — documented in fpdf2 official Streamlit example |
| psycopg2 double-context-manager in st_db.py | Matches api/db.py pattern; conn.close() in finally ensures no connection leak | ✓ Good — consistent with existing Postgres usage |
| init_db() startup in try/except guard | DB unavailability must not crash cold start — app is still useful without Postgres | ✓ Good — app starts without Postgres; save/load degrades gracefully |

## Shipped: v3.0 Advanced Analytics & Multi-Source

All 12 requirements satisfied. 4 phases, 17 plans, 139 tests passing.

Next milestone: start with `/gsd:new-milestone`.

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Current State with shipped version

---
*Last updated: 2026-06-04 — v3.0 Advanced Analytics & Multi-Source milestone shipped*
