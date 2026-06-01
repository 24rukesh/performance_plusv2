# Retrospective — Performance Plus

## Milestone: v1.0-design — User Flow Design Artifacts

**Shipped:** 2026-05-26
**Phases:** 1 | **Plans:** 2 | **Tasks:** 5

### What Was Built

- `01-DESIGN.md` — 126-line design document with system architecture + user flow Mermaid diagrams, frozen 9-column schema, and 20-row PAUSE/INCREASE contrast dataset
- `design/screens/01-load-demo.html` — Streamlit-styled Load Demo Data screen (140 lines)
- `design/screens/02-dataframe-preview.html` — 9-column stitched dataframe preview with IBM Plex Mono table (205 lines)
- `design/screens/03-results.html` — Budget Action Results with 4 badge pill colors (162 lines)

### What Worked

- **Pre-frozen values in PLAN.md** — the `<frozen_values>` blocks in both plans contained exact strings (Mermaid node labels, hex colors, sales note verbatim text) that prevented any drift during execution. Zero D-16 violations.
- **RESEARCH.md and PATTERNS.md** — having these pre-populated before execution meant the executor agents never had to infer conventions; they just read and applied them.
- **Tight acceptance criteria** — grep-based automated checks in the plan caught the DSGN-03 checkbox omission and the D-13 forward-reference violation during task verification, not during UAT.
- **UAT sequence** — 6/6 tests passed on first run; the deliberate quant-vs-qual contradiction in the sample data (high-click PAUSE, low-click INCREASE) made the narrative immediately legible.

### What Was Inefficient

- **REQUIREMENTS.md checkbox gap** — DSGN-03 wasn't checked off during plan execution, requiring a manual fix at milestone close. Plans should explicitly update REQUIREMENTS.md checkboxes on completion.
- **No git remote configured** — `/gsd-ship 1` blocked on missing remote and unauthenticated `gh` CLI, requiring a manual explanation. For hackathon projects, wiring up the remote early avoids this late friction.

### Patterns Established

- **Mermaid node ID convention** — use A,B,C,D,E,F (never `end`, `x`, `o`) to avoid reserved keyword conflicts
- **`<br>` not `<br/>`** in Mermaid node labels (documented in RESEARCH.md, prevented by acceptance criteria)
- **D-16 label consistency contract** — canonical screen labels travel from ROADMAP.md user story → DESIGN.md Mermaid nodes → HTML `<title>` and `<h1>` → UAT test names
- **Badge pill CSS pattern** — `.badge`, `.badge-increase`, `.badge-pause`, `.badge-decrease`, `.badge-insufficient` with exact D-03 hex values

### Key Lessons

1. Frozen values in plan `<context>` blocks eliminate LLM drift on string-precision requirements (label names, hex colors, verbatim quotes). Always pre-populate these before execution.
2. Design-only phases with grep-based acceptance criteria are extremely fast (~2 min/plan) and self-verifying — a good template for future pure-documentation phases.
3. UAT for design artifacts should include a visual browser check of each HTML file, not just grep checks — the tests were structured exactly this way and caught nothing extra, confirming the automated checks covered the surface area well.
4. The PAUSE-vs-INCREASE narrative (cmp_b2b_search high clicks / bad notes vs. cmp_competitor_conquest low clicks / great notes) is the single most compelling thing to demo — make sure the working product preserves this exact contrast in the data generator output.

---

## Cross-Milestone Trends

| Milestone | Plans | Avg/Plan | UAT Pass Rate | Issues Found |
|-----------|-------|----------|---------------|--------------|
| v1.0-design | 2 | 2 min | 6/6 (100%) | 0 |
| v2.0 | 13 | ~5 min | 11/11 (100%) | 0 |

*Updated at each milestone close.*

---

## Milestone: v2.0 — SaaS Foundation

**Shipped:** 2026-06-01
**Phases:** 4 (5–8) | **Plans:** 13 | **Sessions:** 1 (single-day sprint)

### What Was Built

- FastAPI Service — 5 endpoints, API-key auth, Postgres persistence, 14 contract tests
- Waitlist Backend — POST /api/waitlist, Pydantic EmailStr, UNIQUE guard, smtplib STARTTLS notifications to info@k-innovative.com
- Next.js Landing Page — 5-section marketing site, IntersectionObserver animated demo, island architecture, Tailwind v4 @theme
- Streamlit UI Polish — BRANDED_HEADER_HTML, st.expander per-campaign results
- Docker Compose Orchestration — 5-service stack, pg_isready healthcheck, health-gated startup
- Caddy Multi-Route Proxy — / → Next.js, /api/* → FastAPI (prefix preserved), /app* → Streamlit (prefix stripped)

### What Worked

- Wave-based parallel execution for infrastructure plans (2–3 min each)
- Pydantic-first API contract before writing handlers
- S-1 Color Token Mirror pattern locked badge palette cross-stack (Python + TypeScript + Tailwind)
- _make_client monkeypatch helper made all 4 waitlist tests trivial to write
- Single-day sequential execution kept Phase 5 decisions visible when writing Phase 6

### What Was Inefficient

- Stale REQUIREMENTS.md traceability — LAND-01..04 and UI-03..05 stayed "Pending" through UAT; fixed at milestone close
- Missing VERIFICATION.md for Phases 6 and 7 — audit downgraded to "partial" unnecessarily
- Phase 7 Plan 02 (~22 min) dominated by `create-next-app` + package install, not AI generation
- Subagent Bash permission limit stalled Phase 7 Plan 03; orchestrator had to run inline

### Patterns Established

- Pattern S-1: Color Token Mirror — badge hex values must match in `ui_helpers.py`, `badge-tokens.ts`, and `globals.css @theme`
- Pattern DB-3: `psycopg2.extras.Json(result.model_dump())` for JSONB columns
- Pattern: UniqueViolation `except` must be OUTSIDE `with conn:` block (rollback completes first)
- Pattern: Island architecture — static sections as Server Components, single "use client" for interactive form
- Pattern: `.env*` glob in `.dockerignore` + `!.env.example` to block build-time bake-in
- Pattern: `handle /api/*` (preserve prefix) vs `handle_path /app*` (strip prefix) in Caddyfile

### Key Lessons

1. Run `/gsd:verify-phase` at end of every phase — missing it for Phases 6 and 7 created cleanup overhead at milestone close
2. Tailwind v4 silently ignores tailwind.config.ts — all tokens go in `@theme` block in globals.css
3. `NEXT_PUBLIC_*` vars bake into JS bundle at Next.js build time — protect with .env* dockerignore glob + leave var unset in production
4. Same-day sequential execution across dependent phases costs zero sync overhead — linear dependencies don't benefit from parallel workstreams

### Cost Observations

- Model mix: ~100% Sonnet 4.6
- Sessions: 1 (2026-06-01)
- Notable: Infrastructure config plans 2–3 min; code/component plans 5–22 min; Next.js scaffold slowest (22 min, dominated by npm install)
