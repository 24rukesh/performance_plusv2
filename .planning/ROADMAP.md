# Roadmap: Performance Plus — Autonomous Semantic Attribution Engine

## Milestones

- ✅ **v1.0-design — User Flow** — Phase 1 (shipped 2026-05-26)
- ✅ **v1.0 — Working Product** — Phases 2-4 (shipped 2026-05-30)
- ✅ **v2.0 — SaaS Foundation** — Phases 5-8 (shipped 2026-06-01)
- 🚧 **v3.0 — Advanced Analytics & Multi-Source** — Phases 9-12 (in progress)

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

<details>
<summary>✅ v2.0 — SaaS Foundation (Phases 5-8) — SHIPPED 2026-06-01</summary>

- [x] **Phase 5: FastAPI Service** (4/4 plans) — completed 2026-06-01
  - Python FastAPI with 5 endpoints (POST /api/analyze, POST /api/webhook/crm, GET /api/campaigns/{id}/actions, GET /api/health), Postgres result persistence, API key auth, 14 contract tests
- [x] **Phase 6: Waitlist Backend** (2/2 plans) — completed 2026-06-01
  - Waitlist Postgres table, POST /api/waitlist endpoint, Pydantic EmailStr validation, SMTP email notification to info@k-innovative.com on signup
- [x] **Phase 7: Landing Page & UI Polish** (4/4 plans) — completed 2026-06-01
  - Next.js marketing site (hero + waitlist form, How It Works, animated demo cards, features grid, footer) plus Streamlit branded header and expandable results layout
- [x] **Phase 8: Infrastructure Update** (3/3 plans) — completed 2026-06-01
  - Docker Compose adds Next.js + FastAPI + Postgres services, Caddy routes / → Next.js, /api/* → FastAPI, /app* → Streamlit

See archive: `.planning/milestones/v2.0-ROADMAP.md`

</details>

---

### 🚧 v3.0 — Advanced Analytics & Multi-Source (In Progress)

**Milestone Goal:** Transform the single-CSV demo tool into a multi-source analytics platform where marketers upload data from any ads platform + their CRM, get richer AI analysis across sources and currencies, and can save, print, and explore results interactively.

## Phase Details

### Phase 9: Multi-Source Ingestion
**Goal**: Marketers can upload ad platform CSVs from any source with per-file currency selection, map their CRM columns to standard fields via a guided UI, and have all cost data normalized to USD before analysis runs
**Depends on**: Phase 8
**Requirements**: INGEST-01, INGEST-02, INGEST-03
**Success Criteria** (what must be TRUE):
  1. User can add multiple ad platform CSV uploads (Google Ads, Meta Ads, LinkedIn, or custom), assigning a platform name and currency to each before running analysis
  2. User can map their CRM CSV columns to standard fields using an auto-suggest UI that proposes matches and requires explicit confirmation before the merge proceeds
  3. All ad platform cost values are converted to USD via a static FX_RATES dictionary before any aggregation, so cross-platform spend totals are financially meaningful
  4. The merged, normalized DataFrame flows into the existing analysis pipeline without breaking the live app at agent.rukesh.in
**Plans**: 4 plans
Plans:
- [x] 09-01-PLAN.md — ingest.py module: FX_RATES, SUPPORTED_CURRENCIES, ingest() function with source-prefix rename + FX normalization + CRM merge (commit a5f3f6f, 2026-06-02)
- [x] 09-02-PLAN.md — data_generator.py extension + 4 platform fixture CSVs (Google Ads USD, Meta Ads EUR, LinkedIn GBP, Custom USD) (commits 4bbfcf6 + 90835f9, 2026-06-02)
- [x] 09-03-PLAN.md — app.py upload section rewrite: 4-platform grid + CRM mapping UI + sidebar Reporting Currency + Load Demo Data + Run Analysis gate
- [x] 09-04-PLAN.md — tests/test_ingest.py: 24+ unit tests covering FX, happy path, error branches, column collision, CRM mapping

### Phase 10: Richer LLM Analysis
**Goal**: AI recommendations reference cross-platform comparisons and each campaign action identifies which ad platforms contributed to it, while a token preflight guard prevents context window overflow
**Depends on**: Phase 9
**Requirements**: AGENT-01, AGENT-02, AGENT-03
**Success Criteria** (what must be TRUE):
  1. AI budget recommendations explicitly compare platforms (e.g., which platform delivers better lead quality per dollar) based on the unified multi-source dataset
  2. Each campaign action in the results includes a source_platforms list identifying which ad platforms contributed sessions to that campaign
  3. When the aggregated payload approaches 60k tokens, the user sees a warning before the gpt-4o call is made — preventing silent context window overflow
**Plans**: 4 plans
Plans:
- [x] 10-01-PLAN.md — ingest.py CRM extra column pass-through (D-06) + data.py compute_campaign_agg multi-source extension with per-platform pivot, source_platforms column, and crm_ enrichment (D-01 to D-05) (commits 7462345, c31b532, 2026-06-02)
- [x] 10-02-PLAN.md — llm.py: source_platforms field in CampaignAction (D-07), SYSTEM_PROMPT cross-platform + echo rules (D-09 to D-11), count_prompt_tokens helper with o200k_base (D-12 override), fixture_results.json update, tiktoken install (commits 3e6b04a, cda5a78, 2026-06-02)
- [x] 10-03-PLAN.md — app.py: delete Phase 9 bridge block (D-04), add token_warning_confirmed state key, add token gate UI with st.warning + Continue anyway + st.rerun pattern (D-16) (commit 9ecbf14, 2026-06-02)
- [x] 10-04-PLAN.md — tests/test_data.py: multi-source breakdown + source_platforms assertions; tests/test_llm.py: schema required[], count_prompt_tokens, SYSTEM_PROMPT rule tests (49 tests pass, 2026-06-02)

### Phase 11: Charts, Filters & Export
**Goal**: Users can explore analysis results through interactive charts, filter and sort campaigns by any dimension, compare campaigns side-by-side, drill into session-level data, and download results as PDF or CSV
**Depends on**: Phase 10
**Requirements**: VIEW-01, VIEW-02, VIEW-03, MGMT-02
**Success Criteria** (what must be TRUE):
  1. User can view a spend vs qualified leads scatter chart (color-coded by platform) and an action distribution chart for the current analysis, in a tabbed layout alongside the data preview and AI recommendations
  2. User can filter results by platform, action type, and campaign name, and sort results by spend, campaign name, or recommended action
  3. User can select up to 3 campaigns for side-by-side comparison and drill down to session-level rows for any campaign in the results view
  4. User can download the current analysis as a PDF report (via fpdf2) and as a CSV file via st.download_button
**Plans**: 4 plans
Plans:
- [x] 11-01-PLAN.md — Add plotly/fpdf2 deps (uv add) + create pdf_report.py with generate_pdf(result, meta) -> bytes
- [x] 11-02-PLAN.md — Restructure app.py results section into st.tabs + Charts tab (scatter + bar charts, qualified_leads_count inline derivation) (commit 7c766fc, 2026-06-03)
- [x] 11-03-PLAN.md — Campaign Actions tab: Filters & Sort expander, comparison checkboxes (max-3 enforcement), session drill-down inline dataframe, Side-by-Side Comparison section (commits 8b28cad + de4a0e8, 2026-06-03)
- [x] 11-04-PLAN.md — Wire export buttons (PDF + CSV) into Campaign Actions tab; write tests/test_pdf_report.py (5 tests) (commits 7979d9c + de3cc74, 2026-06-03)

### Phase 12: Analysis Persistence
**Goal**: Users can save analyses to Postgres with a label and reload them from a sidebar list without re-uploading CSVs, while the app stays fully functional when the OpenAI API is unavailable
**Depends on**: Phase 11
**Requirements**: MGMT-01, MGMT-03
**Success Criteria** (what must be TRUE):
  1. User can save the current analysis to Postgres with a label, and reload any past saved analysis from a sidebar list without re-uploading CSV files
  2. All saved analyses survive app restart — data persists in the analysis_runs Postgres table with JSONB storage
  3. When the OpenAI API is unavailable, the app falls back to a cached fixture response (DEMO_MODE) so the demo remains functional offline
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 9 → 10 → 11 → 12

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
| 9. Multi-Source Ingestion | v3.0 | 4/4 | Complete | 2026-06-02 |
| 10. Richer LLM Analysis | v3.0 | 4/4 | Complete | 2026-06-02 |
| 11. Charts, Filters & Export | v3.0 | 4/4 | Complete | 2026-06-03 |
| 12. Analysis Persistence | v3.0 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-05-26*
*Last updated: 2026-06-03 — Phase 11 complete: PDF/CSV export buttons wired, 5 test_pdf_report.py tests pass; VIEW-01/02/03 + MGMT-02 delivered*
