# Performance Plus — Autonomous Semantic Attribution Engine

## What This Is

A GenAI-native performance marketing tool that stitches web analytics data with CRM sales notes and uses gpt-4o to translate qualitative lead sentiment into immediate, quantitative ad budget decisions. Built as a hackathon MVP (OpenAI x Outskill AI Builders Cohort 01), now evolved into an early SaaS product with a public marketing site, API layer, waitlist backend, and unified VPS deployment.

The app ingests Web Analytics CSV and CRM CSV files, merges them via `session_id`, sends the unified data to an OpenAI gpt-4o "autonomous CMO" agent, and outputs structured budget action recommendations (increase/pause/decrease by %) alongside semantic reasoning grounded in what sales reps actually said about each lead. External clients can also send session data via the FastAPI service (POST /api/analyze), and visitors can join the waitlist via the Next.js landing page.

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

### Active

Requirements for v3.0 are defined in `.planning/REQUIREMENTS.md`.

### Out of Scope

- Real Meta/Google/LinkedIn Ads API write-back — mock JSON payload only; full API wiring is post-hackathon
- Real CRM/GA data ingestion — synthetic/mock CSV data for the demo
- Full user authentication (login/accounts/sessions) — waitlist-only for now; auth adds 2-3 phases
- Multi-tenant isolation — single-tenant API with API key for current iteration
- Stripe/billing — no paid tier yet (waitlist phase)
- Redis job queue / async background jobs — synchronous API calls sufficient for current scale
- HubSpot/Salesforce direct API pull — generic webhook covers current needs; named CRM integrations are v3+

## Current State

**Version:** v2.0 — SaaS Foundation (shipped 2026-06-01)

**Live at:** https://agent.rukesh.in  
- `/` — Next.js marketing landing page (hero, How It Works, animated demo, features, waitlist form)  
- `/api/*` — FastAPI service (POST /analyze, POST /webhook/crm, GET /health, etc.)  
- `/app` — Streamlit demo app (branded header, expandable campaign results)

**Stack:** Python 3.11 + Streamlit + FastAPI + Pandas + OpenAI gpt-4o + Postgres + Next.js 16 + Tailwind v4 + Docker Compose + Caddy

**Tests:** 81 passing, 5 skipped (pytest) · 11/11 UAT checkpoints passed · TypeScript clean (tsc --noEmit)

**Codebase:** ~2,299 LOC Python + ~450 LOC TypeScript/TSX

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

## Current Milestone: v3.0 Advanced Analytics & Multi-Source

**Goal:** Transform the single-CSV demo tool into a multi-source analytics platform where marketers upload data from any ads platform + their CRM, get richer AI analysis across sources and currencies, and can save, print, and explore results interactively.

**Target features:**
- Multi-source data ingestion (Google Ads, Meta Ads, LinkedIn, custom) with per-upload currency selection and CRM field mapping UI
- Richer agent logic: cross-source/cross-campaign analysis, better prompt engineering with multi-source context
- Dynamic views: charts, filter/sort, side-by-side comparison, session drill-down
- Analysis management: save to Postgres, print/export report, reload saved analyses

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Current State with shipped version

---
*Last updated: 2026-06-01 — v3.0 Advanced Analytics & Multi-Source milestone started*
