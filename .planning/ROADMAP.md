# Roadmap: Performance Plus — Autonomous Semantic Attribution Engine

## Milestones

- ✅ **v1.0-design — User Flow** — Phase 1 (shipped 2026-05-26)
- ✅ **v1.0 — Working Product** — Phases 2-4 (shipped 2026-05-30)
- 🚧 **v2.0 — SaaS Foundation** — Phases 5-8 (in progress)

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
- [ ] **Phase 7: Landing Page & UI Polish** — Next.js marketing site (hero, How It Works, animated demo, features, waitlist form) plus Streamlit branded header and improved results layout
- [ ] **Phase 8: Infrastructure Update** — Docker compose adds Next.js + FastAPI services, Caddy routes all three apps on one domain

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
**Plans**: TBD
**UI hint**: yes

### Phase 8: Infrastructure Update
**Goal**: All three services (Next.js, FastAPI, Streamlit) run as Docker containers on the same VPS and are accessible from a single domain, with Caddy routing / to the landing page, /api to FastAPI, and /app to Streamlit.
**Depends on**: Phase 7
**Requirements**: INFRA-04, INFRA-05, INFRA-06
**Success Criteria** (what must be TRUE):
  1. A browser request to the root domain / serves the Next.js landing page without any manual port specification.
  2. An API request to /api/* is proxied to the FastAPI container and returns the expected response.
  3. A browser request to /app serves the Streamlit app with WebSocket connections maintained (no blank UI).
**Plans**: TBD

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
| 7. Landing Page & UI Polish | v2.0 | 0/? | Not started | - |
| 8. Infrastructure Update | v2.0 | 0/? | Not started | - |

---
*Roadmap created: 2026-05-26*
*Last updated: 2026-06-01 — Phase 6 complete (both plans: waitlist DDL + primitives in 06-01, CORSMiddleware + endpoint + 4 tests in 06-02; WAIT-01/02/03 all done)*
