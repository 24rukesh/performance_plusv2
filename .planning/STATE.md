---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: — SaaS Foundation
status: complete
stopped_at: Phase 8 verified — v2.0 milestone complete
last_updated: "2026-06-01"
last_activity: "2026-06-01 — Phase 8 verified (7/7 passed): landing/Dockerfile + compose.yaml + Caddyfile — all three services routed via Caddy on agent.rukesh.in"
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 13
  completed_plans: 13
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-01 for v2.0 milestone)

**Core value:** A marketer can load demo data and instantly get AI-reasoned budget routing decisions based on what sales reps said about each lead — not just what the click data shows.
**Current focus:** Phase 8 — Infrastructure Update (Docker compose + Caddy routing for Next.js + FastAPI + Streamlit)

## Current Position

Phase: 8 — Infrastructure Update
Plan: 08-03 complete — Phase 8 COMPLETE (3/3 plans)
Status: Phase 8 complete — all plans executed
Last activity: 2026-06-01 — Phase 8 Plan 03 executed: Caddyfile multi-route block — handle /api/* → fastapi:8000, handle_path /app* → app:8501, handle catch-all → landing:3000 (INFRA-06)

## Performance Metrics

**Velocity:**

- Total plans completed: 6
- Average duration: ~5 min/plan (Phase 3 code plans)
- Total execution time: ~15 min (Phase 3)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-design-user-flow-artifacts | 2 | 4 min | 2 min |
| 02-demo-data-foundation | 3 | ~15 min | ~5 min |
| 03-ai-analysis-results-display | 3 | ~15 min | ~5 min |
| 05-fastapi-service (plan 01) | 1 | ~3 min | ~3 min |
| 05-fastapi-service (plan 02) | 1 | ~5 min | ~5 min |
| 05-fastapi-service (plan 03) | 1 | ~5 min | ~5 min |
| 05-fastapi-service (plan 04) | 1 | ~3 min | ~3 min |
| 06-waitlist-backend (plan 01) | 1 | 2 min | 2 min |
| 06-waitlist-backend (plan 02) | 1 | ~2 min | ~2 min |
| 07-landing-page-ui-polish (plan 01) | 1 | 2 min | 2 min |
| 07-landing-page-ui-polish (plan 02) | 1 | ~22 min | ~22 min |
| 08-infrastructure-update (plan 01) | 1 | 2 min | 2 min |
| 08-infrastructure-update (plan 02) | 1 | ~2 min | ~2 min |
| 08-infrastructure-update (plan 03) | 1 | ~2 min | ~2 min |

**Recent Trend:**

- Last 3 plans: 07-02 (~22 min), 07-04 (~5 min), 08-01 (~2 min)
- Trend: infrastructure config plans faster than code plans (~2 min vs ~5 min)

*Updated after each plan completion.*

## Accumulated Context

### Decisions

Key decisions logged in PROJECT.md Key Decisions table. Decisions from v1.0-design milestone:

- D-12: System architecture diagram labels — "Budget Action Recommendations" + "Pydantic Structured Output" edges
- D-16: Four canonical screen labels frozen — Load Demo Data, Stitched Dataframe Preview, Run Analysis, Budget Action Results
- D-05/D-08: 9 CSV column names frozen — web analytics: session_id/campaign_id/clicks/impressions/cost_usd/conversion_rate; CRM: session_id/campaign_id/lead_status/projected_value/sales_notes
- D-03: Badge pill table layout (not card grid) for results screen — 4 colors (#09ab3b/#ff2b2b/#faca2b/#808495)
- D-13: Design doc is presentation material only — no Phase 2/3/4 forward references

Phase 3 decisions:

- LLM model pinned to gpt-4o-2024-08-06 (minimum snapshot for Structured Outputs)
- retry_if_not_exception_type(ValueError) ensures model refusals are not retried
- error_occurred flag pattern for st.status: st.stop() must be outside with-block (Pitfall 6)
- AI-03 verified as behavior (reasoning cites sales-note language), not just schema

v2.0 decisions:

- Caddy routing: / → Next.js, /api → FastAPI, /app → Streamlit — all on same domain (agent.rukesh.in)
- API key auth: X-API-Key header for protected endpoints; stored in env var (no auth on /api/health)
- Waitlist notifications: owner email is info@k-innovative.com, SMTP via Gmail
- Postgres used for two purposes: API result persistence (Phase 5) and waitlist storage (Phase 6)
- UI-03/04/05 consolidated into Phase 7 (Landing Page) as the "product face" phase — avoids a thin standalone Phase 9
- Coarse granularity applied: 4 phases (5-8) rather than 5

Phase 5 Plan 01 decisions:

- psycopg2-binary chosen over asyncpg — sync driver matches FastAPI sync def endpoints
- api/models.py uses BaseModel only (no Field descriptors) — input models don't need LLM schema descriptions
- try/finally conn.close() in all connection-opening functions — with conn: handles transactions only, NOT close
- AnalysisResult/CampaignAction NOT redefined in api/models.py — Plan 03 imports from llm.py directly to prevent schema drift

Phase 5 Plan 02 decisions:

- Non-root appuser (UID/GID 1001) setup duplicated in both runtime stages — intentional, each stage has independent FROM
- Explicit `target: streamlit` on app service in compose.yaml prevents Pitfall 1 (Docker defaulting to last stage = api)
- postgres has no exposed ports — internal Docker bridge only (D-08 constraint)
- fastapi has no exposed ports — Caddy routing for /api deferred to Phase 8 (D-04)
- postgres_data named volume added — Docker-managed, standard practice for synthetic/mock data

Phase 5 Plan 03 decisions:

- All HTTP handlers use sync def (not async def) — run_analysis and psycopg2 are blocking calls; async def would stall the event loop
- APIKeyHeader(auto_error=False) used so verify_api_key raises 401 rather than FastAPI default 403
- No tenacity retry in main.py — llm.py already wraps run_analysis with tenacity (no double-retry)
- No CORS middleware — handled by Caddy reverse proxy at deployment (Phase 8)

Phase 5 Plan 04 decisions:

- Happy path test also mocks insert_analysis_result — required since no DATABASE_URL in CI
- Patch api.main.insert_analysis_result (not api.db) because 'from api.db import' creates local binding
- _make_client helper defers app import until after all monkeypatches are applied

Phase 6 Plan 01 decisions:

- email-validator>=2.0,<3.0 added as explicit dep (pydantic EmailStr requires it — not bundled with pydantic)
- except psycopg2.errors.UniqueViolation placed OUTSIDE with conn: block — ensures context manager completes rollback before except runs (Pitfall 1)
- os.environ["KEY"] bracket access for required SMTP vars (SMTP_HOST/USER/PASS/FROM) — KeyError surfaces misconfiguration immediately
- No try/except in send_waitlist_notification — exceptions propagate to caller for 500 mapping (D-06 fail-loudly)
- RETURNING signed_up_at in INSERT — avoids Python-side datetime drift from DB-generated timestamp

Phase 7 Plan 01 decisions:

- BRANDED_HEADER_HTML placed after load_dotenv() and before st.set_page_config() in source — st.set_page_config remains first Streamlit API call (Pitfall 6)
- build_results_table_html removed from app.py import (prevents ruff F401) but function kept in ui_helpers.py (tests/test_ui_helpers.py depends on it)
- st.expander label is plain-text (Pitfall 2: labels strip HTML); badge HTML rendered inside expander body via st.markdown(unsafe_allow_html=True)

Phase 7 Plan 02 decisions:

- Tailwind v4 @theme block in globals.css (not tailwind.config.ts) — CSS-first config; avoids silent-ignore pitfall
- IBM_Plex_Sans (400, 600) + IBM_Plex_Mono (400) via next/font/google CSS variable pattern — applied to <html> element
- badge-tokens.ts LOCKED hex values must equal ui_helpers.py — cross-stack color invariant (S-1)
- NEXT_PUBLIC_API_BASE_URL left UNSET in production Docker build; Caddy routes /api from same origin (Phase 8)
- landing/.gitignore updated with !.env.example so template file can be committed

Phase 6 Plan 02 decisions:

- CORSMiddleware registered with allow_origins=["*"], no allow_credentials=True — FastAPI rejects wildcard+credentials (D-05)
- POST /api/waitlist has no Depends(verify_api_key) — public endpoint per D-12
- insert_waitlist_email called before send_waitlist_notification — DB commit before email (D-14)
- SMTP exceptions wrapped as HTTPException(500) with "SMTP error:" prefix — fail loudly (D-06)
- Tests patch at api.main.insert_waitlist_email / api.main.send_waitlist_notification binding level (Pitfall 5 — from api.db import creates local binding)

Phase 8 Plan 01 decisions:

- npm ci (no --omit=dev) in builder stage: TypeScript compiler and Tailwind PostCSS are devDependencies needed at build time; standalone copy ensures devDeps never reach runtime image
- HEALTHCHECK omitted from landing/Dockerfile: caddy depends_on for landing has no condition: service_healthy per D-10; adds complexity for no functional benefit in Phase 8
- .env* glob (not bare .env): .env.local contains NEXT_PUBLIC_API_BASE_URL=http://localhost:8000; Next.js reads .env.local at build time; bare .env would not exclude .env.local (Pitfall 4)
- Alpine addgroup/adduser syntax used (not Debian groupadd/useradd): node:20-alpine uses BusyBox; Debian syntax causes sh: useradd: not found (Pitfall 1)

Phase 8 Plan 02 decisions:

- Postgres healthcheck values: interval 10s, timeout 5s, retries 5, start_period 30s — conventional community values per RESEARCH.md A1 (Claude's Discretion area)
- caddy depends_on uses list form (not dict form with condition) per D-10 — no health-gating on caddy startup, restart: unless-stopped provides recovery
- landing service has no env_file key — NEXT_PUBLIC_* vars baked at build time, no server-side secrets per D-14/T-08-07
- landing service has no target key in build — landing/Dockerfile has only one output stage (runner) as default last stage

Phase 8 Plan 03 decisions:

- handle /api/* (not handle_path) preserves /api/ prefix — all FastAPI routes are /api/-prefixed; stripping would 404 every route (D-07)
- handle_path /app* (not /app/*) — /app* glob matches bare /app and /app/anything; /app/* would miss bare /app (Pitfall 2, D-06)
- Catch-all handle placed last — Caddy first-match-wins evaluation order enforced in document order (D-09)
- No explicit Upgrade/Connection headers — Caddy reverse_proxy auto-upgrades WebSocket; prevents #1 Streamlit self-hosted proxy bug

### Pending Todos

None.

### Blockers/Concerns

None.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| DEMO_MODE fallback | Cached fixture results when OpenAI unavailable | Deferred | Phase 3 |
| tiktoken preflight | Token counting before sending to gpt-4o | Deferred | Phase 3 |
| Export CSV button | Export results as CSV | Deferred | Phase 3 |

## Session Continuity

Last session: 2026-06-01
Stopped at: Phase 8 Plan 03 complete — Caddyfile multi-route block committed (cf5f7fe). Phase 8 COMPLETE.
Resume file: None — milestone v2.0 complete
