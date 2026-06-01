# Roadmap: Performance Plus — Autonomous Semantic Attribution Engine

## Milestones

- ✅ **v1.0-design — User Flow** — Phase 1 (shipped 2026-05-26)
- ✅ **v1.0 — Working Product** — Phases 2-4 (shipped 2026-05-30)
- ✅ **v2.0 — SaaS Foundation** — Phases 5-8 (shipped 2026-06-01)

## Phases

<details>
<summary>✅ v1.0-design — User Flow (Phase 1) — SHIPPED 2026-05-26</summary>

- [x] Phase 1: Design & User Flow Artifacts (2/2 plans) — completed 2026-05-26
  - [x] 01-01: 01-DESIGN.md — System architecture + user flow diagrams + frozen schema + 20-row sample data
  - [x] 01-02: 3 Streamlit-styled HTML screen mockups (Load Demo Data, Stitched Dataframe Preview, Budget Action Results)

See archive: `.planning/milestones/v1.0-design-ROADMAP.md`

</details>

<details>
<summary>✅ v1.0 — Working Product (Phases 2-4) — SHIPPED 2026-05-30</summary>

- [x] Phase 2: Demo Data Foundation (3/3 plans) — completed 2026-05-29
- [x] Phase 3: AI Analysis & Results Display (3/3 plans) — completed 2026-05-30
- [x] Phase 4: Deploy & Ship (3/3 plans) — completed 2026-05-30

</details>

---

### 🚧 v2.0 — SaaS Foundation (Phases 5-8)

Four vertical slices that evolve the hackathon MVP into a publicly marketed SaaS product with an API layer, waitlist backend, marketing site, and unified VPS deployment.

- [x] **Phase 5: FastAPI Service** — Python FastAPI with five API endpoints, Postgres for result persistence, API key auth
- [x] **Phase 6: Waitlist Backend** — Waitlist Postgres table, POST /api/waitlist endpoint, SMTP email notification on signup
- [x] **Phase 7: Landing Page & UI Polish** — Next.js marketing site (hero, How It Works, animated demo, features, waitlist form) plus Streamlit branded header and improved results layout
- [x] **Phase 8: Infrastructure Update** — Docker compose adds Next.js + FastAPI services, Caddy routes all three apps on one domain

## Phase Details

### Phase 5: FastAPI Service

**Goal**: An authorized external client (n8n, CRM webhook, API consumer) can send session data to a FastAPI service and receive structured gpt-4o budget action recommendations, with results persisted in Postgres for later retrieval.
**Depends on**: Phase 4
**Requirements**: API-01, API-02, API-03, API-04, API-05
**Success Criteria** (what must be TRUE):

  1. A client sending a valid X-API-Key header and JSON payload to POST /api/analyze receives a structured JSON response with per-campaign budget actions from gpt-4o.
  2. A client sending an invalid or missing X-API-Key header to any protected endpoint receives a 401 response.
  3. Analysis results from POST /api/analyze are stored in Postgres keyed by campaign ID and timestamp, and a subsequent GET /api/campaigns/{campaign_id}/actions returns that result.
  4. A client can POST /api/webhook/crm with a normalized CRM lead payload and receive a 202 acknowledgement, with the session ingested for future analysis.
  5. Any client (no auth required) can GET /api/health and receive a 200 response with service status and version string.

**Plans:** 4 plans
  **Wave 1** *(parallel — no dependencies)*

  - [x] 05-01-PLAN.md — api/ package scaffold: models.py + db.py + dependency additions to pyproject.toml + .env.example
  - [x] 05-02-PLAN.md — Dockerfile multi-target rewrite + compose.yaml adds fastapi + postgres services
  **Wave 2** *(blocked on Wave 1 completion)*

  - [x] 05-03-PLAN.md — api/main.py: FastAPI app, lifespan(init_db), verify_api_key dependency, all 5 endpoints
  **Wave 3** *(blocked on Wave 2 completion)*

  - [x] 05-04-PLAN.md — tests/test_api.py: pytest + TestClient contract tests for all 5 endpoints + auth + persistence

  **Cross-cutting constraints:**

  - psycopg2 raw parameterized SQL — no ORM, no SQLAlchemy (D-09)
  - All protected endpoints use verify_api_key FastAPI dependency; /api/health has no auth (D-12)
  - Sync `def` endpoints only — run_analysis() is blocking; async def would stall the event loop

### Phase 6: Waitlist Backend

**Goal**: A visitor can submit their email address and be immediately acknowledged, with the signup stored in Postgres and the product owner notified by email at info@k-innovative.com.
**Depends on**: Phase 5
**Requirements**: WAIT-01, WAIT-02, WAIT-03
**Success Criteria** (what must be TRUE):

  1. A visitor who submits the waitlist form receives an on-page confirmation message within seconds.
  2. The submitted email and signup timestamp appear in the Postgres waitlist table immediately after submission.
  3. The product owner receives an SMTP email at info@k-innovative.com containing the submitted email address and timestamp within one minute of signup.

**Plans:** 2 plans
  **Wave 1** *(parallel — no dependencies)*

  - [x] 06-01-PLAN.md — Foundations: email-validator dep, .env.example SMTP vars, waitlist table + insert_waitlist_email, WaitlistRequest model, api/email_utils.py SMTP helper
  **Wave 2** *(blocked on Wave 1 completion)*

  - [x] 06-02-PLAN.md — Wire endpoint + tests: CORSMiddleware, POST /api/waitlist public handler, 4 contract tests (200/422/409/500)

### Phase 7: Landing Page & UI Polish

**Goal**: A visitor landing on the root domain sees a polished marketing page that explains the product, shows an animated demo, and lets them join the waitlist — while existing Streamlit users see a branded header with a link back to the marketing site.
**Depends on**: Phase 6
**Requirements**: LAND-01, LAND-02, LAND-03, LAND-04, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):

  1. A visitor can read a hero section with the product name, one-liner value prop, a "Try Demo" CTA that opens the Streamlit app, and a "Join Waitlist" CTA.
  2. A visitor can read a "How It Works" section showing the Upload → AI Analysis → Budget Decisions 3-step flow.
  3. A visitor can see an inline animated demo preview of campaign cards with action badges without leaving the page.
  4. A visitor can read a Features section covering semantic attribution, CRM webhook sync, n8n automation, and budget routing.
  5. A Streamlit app user can see the Performance Plus branded header with icon, tagline, and a visible link to the marketing landing page, with campaign results displayed in an improved expandable layout.

**Plans:** 4 plans
  **Wave 1** *(parallel — no dependencies)*

  - [x] 07-01-PLAN.md — Streamlit polish (UI-03, UI-04, UI-05): branded header HTML constant + `st.expander` per-campaign loop replacing `build_results_table_html`, import line refactored without removing the function from `ui_helpers.py`
  - [x] 07-02-PLAN.md — Next.js scaffold + foundation (LAND-01 prep): `create-next-app` for `landing/`, Tailwind v4 `@theme` brand/badge tokens + `fadeSlideIn` keyframe in `globals.css`, IBM Plex Sans/Mono via `next/font/google` in `layout.tsx`, shared `components/badge-tokens.ts` mirror, `.env.example`/`.env.local` documenting `NEXT_PUBLIC_API_BASE_URL`
  **Wave 2** *(blocked on 07-02)*

  - [x] 07-03-PLAN.md — Hero + WaitlistForm + HowItWorks (LAND-01, LAND-02): `WaitlistForm.tsx` client island with 5-state status machine fetching `/api/waitlist`, Hero Server Component with locked UI-SPEC copy + dual CTAs, `HowItWorksSection.tsx` 3-step responsive grid, `page.tsx` composes top half
  **Wave 3** *(blocked on 07-03)*

  - [x] 07-04-PLAN.md — DemoAnimation + Features + Footer + verification (LAND-03, LAND-04): `DemoAnimation.tsx` client island with IntersectionObserver-gated CSS keyframes + 4 hardcoded campaign cards, `FeaturesSection.tsx` 4-card grid with Heroicons, `Footer.tsx`, final `page.tsx` composition, `npm run build` + `pytest` gates

  **Cross-cutting constraints:**

  - No Docker/Caddy changes in Phase 7 — Phase 8 owns infrastructure wiring (per ROADMAP Phase 8 boundary)
  - Tailwind v4 only — NO `tailwind.config.ts` (Pitfall 1: v4 ignores it silently); all tokens in `@theme` block in `globals.css`
  - `NEXT_PUBLIC_API_BASE_URL` must remain UNSET in production (Pitfall 3); set only in `landing/.env.local` for local dev
  - `build_results_table_html` MUST remain in `ui_helpers.py` (tests/test_ui_helpers.py still imports it) — only the `app.py` import is pruned
  - Locked badge palette (`#09ab3b`, `#ff2b2b`, `#faca2b` w/ `#262730` text, `#808495`) MUST appear identically in `ui_helpers.py`, `landing/components/badge-tokens.ts`, and the `@theme` block (PATTERNS.md §S-1)

### Phase 8: Infrastructure Update

**Goal**: All three services (Next.js, FastAPI, Streamlit) run as Docker containers on the same VPS and are accessible from a single domain, with Caddy routing / to the landing page, /api to FastAPI, and /app to Streamlit.
**Depends on**: Phase 7
**Requirements**: INFRA-04, INFRA-05, INFRA-06
**Success Criteria** (what must be TRUE):

  1. A browser request to the root domain / serves the Next.js landing page without any manual port specification.
  2. An API request to /api/* is proxied to the FastAPI container and returns the expected response.
  3. A browser request to /app serves the Streamlit app with WebSocket connections maintained (no blank UI).

**Plans:** 3/3 plans executed
  **Wave 1** *(parallel — no dependencies)*

  - [x] 08-01-PLAN.md — Next.js standalone build (INFRA-04): `landing/next.config.ts` adds `output: 'standalone'`, new `landing/.dockerignore` with `.env*` glob (Pitfall 4 guard), new `landing/Dockerfile` (node:20-alpine multi-stage with Alpine `addgroup`/`adduser` for UID 1001 appuser, exact public→standalone→static COPY order)
  **Wave 2** *(blocked on 08-01)*

  - [x] 08-02-PLAN.md — Compose orchestration (INFRA-04, INFRA-05): `compose.yaml` adds `landing` service (no ports, no env_file), `postgres` healthcheck via `pg_isready`, `fastapi` depends_on dict form with `condition: service_healthy` (Pitfall 6), `caddy` depends_on list extended to `[app, fastapi, landing]`
  - [x] 08-03-PLAN.md — Caddy multi-route (INFRA-06): `caddy/Caddyfile` replaced with three-handler block — `handle /api/*` → fastapi:8000 (prefix preserved), `handle_path /app*` → app:8501 (prefix stripped, glob `/app*` not `/app/*` per Pitfall 2), `handle` catch-all → landing:3000

  **Cross-cutting constraints:**

  - Pure infrastructure phase — zero application code changes (no .py, no .ts component files modified)
  - All three services internal-only — only `caddy` publishes ports 80/443 (T-08-06 guard)
  - `landing/Dockerfile` MUST NOT have any `NEXT_PUBLIC_*` ARG/ENV (D-14 from Phase 7; T-08-03 / Pitfall 4 guard)
  - `tests/test_deploy_config.py` all 7 invariant tests continue to pass — `reverse_proxy app:8501` substring survives inside new `handle_path /app*` block (Pitfall 3)
  - Docker build/Caddy validate deferred to VPS deploy-time (Docker not present in local Mac dev shell per RESEARCH.md Environment Availability)

## Progress

**Execution Order:** Phases execute in numeric order: 5 → 6 → 7 → 8

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Design & User Flow Artifacts | v1.0-design | 2/2 | ✅ Complete | 2026-05-26 |
| 2. Demo Data Foundation | v1.0 | 3/3 | ✅ Complete | 2026-05-29 |
| 3. AI Analysis & Results Display | v1.0 | 3/3 | ✅ Complete | 2026-05-30 |
| 4. Deploy & Ship | v1.0 | 3/3 | ✅ Complete | 2026-05-30 |
| 5. FastAPI Service | v2.0 | 4/4 | ✅ Complete | 2026-06-01 |
| 6. Waitlist Backend | v2.0 | 2/2 | ✅ Complete | 2026-06-01 |
| 7. Landing Page & UI Polish | v2.0 | 4/4 | ✅ Complete | 2026-06-01 |
| 8. Infrastructure Update | v2.0 | 3/3 | ✅ Complete | 2026-06-01 |

---
*Roadmap created: 2026-05-26*
*Last updated: 2026-06-01 — Phase 8 Plan 03 complete (3/3): Caddyfile three-route block (INFRA-06). Phase 8 complete. Milestone v2.0 complete.*
