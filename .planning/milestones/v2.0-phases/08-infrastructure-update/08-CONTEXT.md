# Phase 8: Infrastructure Update - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire all three application services (Next.js landing page, FastAPI backend, Streamlit app) into a single Docker Compose deployment on the VPS, with Caddy routing traffic from one domain to all three.

Concrete deliverables:
- `landing/Dockerfile` — multi-stage Node.js build for the Next.js container
- `landing/next.config.ts` — add `output: 'standalone'` for production Docker
- `compose.yaml` — add `landing` service, update `caddy` and `fastapi` dependencies
- `caddy/Caddyfile` — replace single-service proxy with multi-route config:
  - `/` → Next.js (landing:3000)
  - `/api/*` → FastAPI (fastapi:8000) — prefix preserved
  - `/app/*` → Streamlit (app:8501) — prefix stripped

Phase 8 scope ONLY: Docker and Caddy configuration. No application code changes.

</domain>

<decisions>
## Implementation Decisions

### Next.js Dockerfile
- **D-01:** Location: `landing/Dockerfile` — dedicated file inside `landing/` directory. `compose.yaml` references it with `build: { context: ./landing }`. Keeps Node.js build toolchain completely separate from the Python Dockerfile.
- **D-02:** Node base image: `node:20-alpine` — Node 20 LTS on Alpine (~130 MB). Use multi-stage build (builder stage installs deps + builds; runtime stage copies only the standalone bundle).
- **D-03:** Internal port: **3000** (Next.js default). Caddy proxies to `landing:3000` internally. Port is never exposed to the host.

### Next.js Production Output Mode
- **D-04:** Add `output: 'standalone'` to `next.config.ts`. Next.js emits `.next/standalone/` with the minimum server bundle — no `node_modules` in the runtime Docker image. The `landing/Dockerfile` copies `.next/standalone`, `.next/static`, and `public/` per Next.js standalone instructions.
- **D-05:** Non-root appuser: Create `appgroup` (GID 1001) + `appuser` (UID 1001) in `landing/Dockerfile` — consistent with the pattern in the root `Dockerfile` for Streamlit and FastAPI stages.

### Caddy Routing
- **D-06:** `/app/*` → Streamlit: Use `handle_path /app* { reverse_proxy app:8501 }` — Caddy **strips** the `/app` prefix before proxying. Streamlit receives requests at `/` with no `--server.baseUrlPath` change required. CMD in the `streamlit` Dockerfile stage is unchanged.
- **D-07:** `/api/*` → FastAPI: Use `handle /api/* { reverse_proxy fastapi:8000 }` — Caddy does **NOT** strip the prefix. All FastAPI routes in `api/main.py` include the `/api/` prefix (`/api/health`, `/api/analyze`, `/api/webhook/crm`, etc.). Stripping would break every route.
- **D-08:** `/` → Next.js: Catch-all at the bottom of the Caddyfile — `handle { reverse_proxy landing:3000 }`.
- **D-09:** Route ordering in Caddyfile: `/api/*` first, `/app/*` second, catch-all `/` last. Caddy evaluates most-specific first but explicit ordering makes intent clear.

### Service Startup Ordering (compose.yaml)
- **D-10:** `caddy` depends_on: `[app, fastapi, landing]` — simple list, no `condition: service_healthy`. Caddy starts after all three service containers start (not after they're healthy). `restart: unless-stopped` on all services handles recovery.
- **D-11:** `fastapi` depends_on postgres with `condition: service_healthy`. Add a `healthcheck` to the `postgres` service using `pg_isready` to prevent the startup race where FastAPI `init_db` runs before Postgres accepts connections.
  - Suggested postgres healthcheck: `pg_isready -U ppuser -d performance_plus`

### Claude's Discretion
- Exact `healthcheck` interval/timeout/retries values for the postgres healthcheck.
- Whether to add a HEALTHCHECK to `landing/Dockerfile` (not required — caddy depends_on is not healthcheck-gated for the landing service).
- `npm ci --omit=dev` vs `npm ci` in the landing builder stage.
- Exact `CMD` for the standalone Next.js server (`node server.js` from `.next/standalone/`).
- Caddyfile formatting and comment style.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `./CLAUDE.md` — Stack constraints. Read "TL;DR", "What NOT to Use" (Nginx default config drops WebSocket; Caddy auto-handles WS), and "Risk Register" (Streamlit WebSocket dropped by proxy is the #1 self-hosted bug).
- `.planning/PROJECT.md` — v2.0 goals, current state, constraints.
- `.planning/ROADMAP.md` — Phase 8 goal, success criteria (3 items), requirements INFRA-04/05/06.
- `.planning/REQUIREMENTS.md` §Infrastructure — full text of INFRA-04, INFRA-05, INFRA-06.

### Existing Infrastructure to Modify
- `./compose.yaml` — Current services: `app` (Streamlit), `caddy`, `fastapi`, `postgres`. Missing: `landing` service. `caddy` currently only `depends_on: [app]`.
- `./caddy/Caddyfile` — Current: single `agent.rukesh.in { reverse_proxy app:8501 }` block. Must become a multi-route config.
- `./Dockerfile` — Multi-stage Python build (builder → streamlit → api targets). Reference for `appgroup`/`appuser` (GID/UID 1001) pattern to replicate in `landing/Dockerfile`.

### New Files to Create
- `./landing/Dockerfile` — Does not exist yet. Node 20-alpine multi-stage build for Next.js standalone output.
- `./landing/next.config.ts` — Currently has empty config. Must add `output: 'standalone'`.

### Prior Phase Decisions
- `.planning/phases/05-fastapi-service/` — D-04 (fastapi has no exposed ports — Caddy routing deferred to Phase 8); D-08 (postgres has no exposed ports — internal Docker bridge only).
- `.planning/phases/07-landing-page-ui-polish/07-CONTEXT.md` — D-14 (`NEXT_PUBLIC_API_BASE_URL` left UNSET in production; Caddy routes `/api` from same origin); D-04 (`build.context: ./landing` for compose landing service).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `./Dockerfile` (lines 28–50, streamlit stage; lines 53–75, api stage): `appgroup`/`appuser` creation pattern — replicate exactly in `landing/Dockerfile` runtime stage for consistent security posture.
- `./compose.yaml`: `internal` bridge network already defined — `landing` service joins it without changes to the network block.

### Established Patterns
- `restart: unless-stopped` on all app services — maintain for `landing` as well.
- `env_file: .env` on `app` and `fastapi` — `landing` may not need env_file (no server-side secrets; `NEXT_PUBLIC_*` are baked at build time).
- `postgres_data` named volume — already defined; no changes needed for Phase 8.

### Integration Points
- `caddy/Caddyfile`: single reverse_proxy becomes a three-route matcher. Caddy 2 `handle` and `handle_path` directives (within a named site block) are the mechanism.
- FastAPI routes all start with `/api/` — confirmed by grepping `api/main.py`. Caddy must NOT strip this prefix.
- Streamlit currently serves at `/` — path stripping in `handle_path /app*` lets it continue doing so.
- `NEXT_PUBLIC_API_BASE_URL`: unset in production build → fetch calls resolve to relative `/api/waitlist` → Caddy routes to FastAPI correctly.

</code_context>

<specifics>
## Specific Ideas

- The Caddyfile host block is `agent.rukesh.in`. All three route matchers live inside this single site block — one TLS cert covers all three services.
- Postgres healthcheck command: `["CMD-SHELL", "pg_isready -U ppuser -d performance_plus"]` (matches the DB user and name already in compose.yaml).
- Next.js standalone CMD: `node server.js` run from the `.next/standalone/` directory (standard standalone pattern).
- HEALTHCHECK in `landing/Dockerfile` can use `wget -qO- http://localhost:3000/` or skip it (caddy's depends_on is not healthcheck-gated for landing).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-infrastructure-update*
*Context gathered: 2026-06-01 via discuss-phase*
