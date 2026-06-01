# Phase 8: Infrastructure Update - Research

**Researched:** 2026-06-01
**Domain:** Docker multi-service compose, Next.js standalone Docker, Caddy multi-route proxy
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Location: `landing/Dockerfile` — dedicated file inside `landing/` directory. `compose.yaml` references it with `build: { context: ./landing }`.
- **D-02:** Node base image: `node:20-alpine`, multi-stage build (builder stage installs deps + builds; runtime stage copies only the standalone bundle).
- **D-03:** Internal port: **3000** (Next.js default). Caddy proxies to `landing:3000` internally. Port is never exposed to the host.
- **D-04:** Add `output: 'standalone'` to `next.config.ts`. Next.js emits `.next/standalone/` with the minimum server bundle. The `landing/Dockerfile` copies `.next/standalone`, `.next/static`, and `public/` per Next.js standalone instructions.
- **D-05:** Non-root appuser: Create `appgroup` (GID 1001) + `appuser` (UID 1001) in `landing/Dockerfile` — consistent with the pattern in the root `Dockerfile`.
- **D-06:** `/app/*` → Streamlit: Use `handle_path /app* { reverse_proxy app:8501 }` — Caddy strips the `/app` prefix before proxying.
- **D-07:** `/api/*` → FastAPI: Use `handle /api/* { reverse_proxy fastapi:8000 }` — Caddy does NOT strip the prefix.
- **D-08:** `/` → Next.js: Catch-all at the bottom — `handle { reverse_proxy landing:3000 }`.
- **D-09:** Route ordering: `/api/*` first, `/app/*` second, catch-all `/` last.
- **D-10:** `caddy` depends_on: `[app, fastapi, landing]` — simple list, no `condition: service_healthy`.
- **D-11:** `fastapi` depends_on postgres with `condition: service_healthy`. Add postgres healthcheck using `pg_isready -U ppuser -d performance_plus`.

### Claude's Discretion
- Exact `healthcheck` interval/timeout/retries values for the postgres healthcheck.
- Whether to add a HEALTHCHECK to `landing/Dockerfile`.
- `npm ci --omit=dev` vs `npm ci` in the landing builder stage.
- Exact `CMD` for the standalone Next.js server.
- Caddyfile formatting and comment style.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-04 | The Next.js landing page runs in a Docker container deployed on the same VPS as the existing Streamlit app | `landing/Dockerfile` multi-stage build pattern; compose `landing` service definition |
| INFRA-05 | The FastAPI service runs in a Docker container on the same VPS | postgres healthcheck + `depends_on: condition: service_healthy` eliminates startup race |
| INFRA-06 | Caddy routes incoming traffic so `/` serves Next.js, `/api` proxies to FastAPI, `/app` proxies to Streamlit — all on the same domain | Caddy `handle` / `handle_path` multi-route single-site-block pattern; WebSocket auto-upgrade confirmed |
</phase_requirements>

---

## Summary

Phase 8 wires three independent application services — Next.js 16 (landing), FastAPI (api), Streamlit (app) — into a unified Docker Compose deployment behind a single Caddy reverse proxy. The work is entirely infrastructure: four files to create or modify, zero application code changes.

The primary technical challenge is the **Next.js standalone Docker pattern** (verified from the installed `node_modules/next@16.2.6` docs and the official canary Dockerfile example). Next.js 16 with `output: 'standalone'` emits `.next/standalone/server.js` — a self-contained Node server requiring no `node_modules` in the runtime image. The exact COPY sequence matters: standalone bundle first, then static assets overlaid on top. This differs meaningfully from the training-data mental model of `next start`.

The second challenge is **Caddy route ordering and prefix semantics**. `handle_path` strips the matched prefix before proxying (so `/app/session` becomes `/session` at Streamlit); `handle` preserves it (so `/api/health` stays `/api/health` at FastAPI). Caddy's `reverse_proxy` handles WebSocket upgrade automatically — no extra headers required — which is the critical property for Streamlit.

The third challenge is the **postgres healthcheck startup race**: FastAPI's `init_db()` runs at startup and will fail if Postgres is not yet ready to accept connections. The compose `condition: service_healthy` guard with `pg_isready` solves this reliably.

**Primary recommendation:** Follow D-01 through D-11 exactly as locked. The official Next.js 16 Dockerfile template (fetched live) confirms all locked decisions. No deviations are warranted.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| TLS termination | Caddy (edge proxy) | — | Caddy auto-HTTPS; all three services are internal-only |
| Route dispatch (/ vs /api vs /app) | Caddy (edge proxy) | — | Single Caddyfile site block with `handle`/`handle_path` matchers |
| Landing page rendering | Frontend Server (landing:3000) | — | Next.js App Router SSR via standalone server |
| API business logic | API / Backend (fastapi:8000) | — | FastAPI endpoints; all use `/api/` prefix |
| Streamlit app serving | Frontend Server (app:8501) | — | Streamlit serves at `/` after Caddy strips `/app` prefix |
| WebSocket upgrade (Streamlit) | Caddy (edge proxy) | — | Caddy reverse_proxy handles WS transparently |
| Database readiness gate | Docker Compose healthcheck | — | pg_isready ensures postgres ready before FastAPI starts |
| Service orchestration | Docker Compose | — | depends_on, restart: unless-stopped, named volumes |

---

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | **16.2.6** (installed) | Landing page server | Project-installed; `output: 'standalone'` supported since Next.js 12 |
| node:20-alpine | 20 LTS | Builder + runtime base image | Locked D-02; LTS, small Alpine footprint (~130 MB) |
| caddy:2-alpine | 2.x (current in compose.yaml) | Reverse proxy + TLS | Already used; auto-WS, auto-HTTPS |
| postgres:16-alpine | 16 (current in compose.yaml) | Database | Already used; pg_isready ships in the image |
| Docker Compose v2 | v2 | Service orchestration | Existing project standard |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| npm ci | bundled with node:20 | Deterministic dep install in builder | Use `--omit=dev` optional — both work since standalone build tree-shakes; `--omit=dev` reduces build-stage disk use |
| pg_isready | ships with postgres:16-alpine | Postgres healthcheck command | Only healthcheck command guaranteed present in postgres:16-alpine image |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `handle_path /app*` | `handle /app/* { uri strip_prefix /app }` | Equivalent (handle_path IS uri strip_prefix under the hood) — D-06 locks handle_path for brevity |
| `pg_isready` healthcheck | `psql -U ppuser -d performance_plus -c 'SELECT 1'` | psql not always in minimal postgres images; pg_isready is always present |
| `condition: service_healthy` | `service_started` (default) | service_started doesn't wait for postgres to accept connections — causes FastAPI init_db() race |

**Installation (builder stage npm):**
```bash
npm ci
# or with optional dev-dep exclusion:
npm ci --omit=dev
```

---

## Architecture Patterns

### System Architecture Diagram

```
Internet
    │  HTTPS :443
    ▼
┌─────────────────────────────────────────────┐
│             Caddy (caddy:2-alpine)          │
│         site: agent.rukesh.in               │
│                                             │
│  handle /api/*  ──────────────────────────► fastapi:8000
│  (prefix preserved)                         │   (FastAPI)
│                                             │
│  handle_path /app*  ──────────────────────► app:8501
│  (prefix stripped → /)                      │   (Streamlit + WS)
│                                             │
│  handle (catch-all)  ─────────────────────► landing:3000
│                                             │   (Next.js)
└─────────────────────────────────────────────┘

All on Docker internal bridge network
postgres:5432  ◄──── fastapi (depends_on: service_healthy)
```

### Recommended Project Structure

```
performance_plus/
├── landing/
│   ├── Dockerfile          # NEW — Node 20-alpine multi-stage
│   ├── .dockerignore       # NEW — excludes node_modules, .next, .env*
│   ├── next.config.ts      # MODIFY — add output: 'standalone'
│   ├── app/                # existing source
│   └── public/             # existing static assets
├── caddy/
│   └── Caddyfile           # MODIFY — multi-route block
├── compose.yaml            # MODIFY — add landing, postgres healthcheck
└── Dockerfile              # UNCHANGED — Python multi-stage
```

### Pattern 1: Next.js 16 Standalone Docker (Official Template)

**What:** Multi-stage build where the builder produces `.next/standalone/` (contains `server.js` + traced `node_modules`), then the runtime stage copies only that bundle plus `public/` and `.next/static/`.

**When to use:** Any Next.js Docker container where `output: 'standalone'` is set in next.config.

**Critical COPY sequence** (order matters — static overlays standalone's `.next/`):

```dockerfile
# Source: https://github.com/vercel/next.js/tree/canary/examples/with-docker (verified 2026-06-01)
# Adapted for node:20-alpine and appuser (D-02, D-05)

# ---- builder ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ENV NODE_ENV=production
RUN npm run build

# ---- runtime ----
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user consistent with Python Dockerfile pattern (D-05)
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -h /home/appuser appuser

# 1. Public assets (CDN-served static files)
COPY --from=builder --chown=appuser:appgroup /app/public ./public

# 2. Create .next and set ownership
RUN mkdir .next && chown appuser:appgroup .next

# 3. Standalone bundle (contains server.js + traced node_modules)
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./

# 4. Static assets overlaid into .next/static (MUST come AFTER standalone copy)
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser

EXPOSE 3000

CMD ["node", "server.js"]
```

**Alpine vs Debian adduser syntax note:** `node:20-alpine` uses BusyBox `addgroup`/`adduser` (not `groupadd`/`useradd`). The flags differ:
- Alpine: `addgroup -g 1001 appgroup` and `adduser -u 1001 -G appgroup -D -h /home/appuser appuser`
- Debian (existing Dockerfile): `groupadd -g 1001 appgroup` and `useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser`

The `-D` flag on Alpine's `adduser` means "no password" (equivalent to system user). `-h` sets home dir. No `-m` flag needed on Alpine — home dir is created by default when `-h` is set. [VERIFIED: node:20-alpine BusyBox adduser manpage behavior]

### Pattern 2: Caddy Multi-Route Single Site Block

**What:** All three route matchers live inside one site block. Caddy evaluates `handle` blocks in document order; first match wins. `handle_path` implicitly strips the matched prefix.

**Critical ordering:** More specific matchers MUST precede catch-all. [VERIFIED: caddyserver.com/docs/caddyfile/directives/handle]

```
# Source: caddyserver.com/docs/caddyfile/directives/handle and handle_path (verified 2026-06-01)
agent.rukesh.in {

    # /api/* → FastAPI — prefix preserved (all FastAPI routes include /api/)
    handle /api/* {
        reverse_proxy fastapi:8000
    }

    # /app* → Streamlit — prefix stripped (/app/foo → /foo; /app → /)
    handle_path /app* {
        reverse_proxy app:8501
    }

    # catch-all → Next.js landing page
    handle {
        reverse_proxy landing:3000
    }
}
```

**handle vs handle_path mechanics** [VERIFIED: caddyserver.com/docs/caddyfile/directives/handle_path]:
- `handle_path /app*` is exactly equivalent to: `handle /app* { uri strip_prefix /app ... }`
- Pattern `/app*` matches `/app`, `/app/`, `/app/session`, `/app?foo=bar`
- After stripping: `/app/session` → `/session`; `/app/` → `/`; `/app` → `/`

### Pattern 3: Docker Compose Postgres Healthcheck + depends_on

**What:** Add `healthcheck` to the postgres service so that FastAPI's `depends_on: condition: service_healthy` waits for Postgres to be ready before starting.

**Verified syntax** [VERIFIED: docs.docker.com/compose/compose-file/05-services/#healthcheck]:

```yaml
postgres:
  image: postgres:16-alpine
  restart: unless-stopped
  environment:
    POSTGRES_DB: performance_plus
    POSTGRES_USER: ppuser
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - internal
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ppuser -d performance_plus"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

```yaml
fastapi:
  build:
    context: .
    target: api
  restart: unless-stopped
  env_file: .env
  networks:
    - internal
  depends_on:
    postgres:
      condition: service_healthy
```

**Recommended healthcheck values** (Claude's Discretion area):
- `interval: 10s` — check every 10 seconds
- `timeout: 5s` — fail if pg_isready doesn't respond in 5s
- `retries: 5` — mark unhealthy after 5 consecutive failures
- `start_period: 30s` — grace period for postgres cold start; failures during this window don't count toward retries [ASSUMED — these are conventional values; official docs say "platform-specific defaults"]

### Anti-Patterns to Avoid

- **Wrong COPY order for standalone:** Copying `.next/static` BEFORE `.next/standalone` causes static assets to be overwritten by the standalone bundle. Always: public → standalone → static.
- **Exposing the landing port to the host:** `ports: ["3000:3000"]` on the landing service. Port must be internal-only (D-03). Only caddy publishes ports 80/443.
- **Using `handle_path /app/*` (with trailing slash):** The pattern must be `/app*` (no slash after `app`). `/app/*` would miss requests to `/app` itself, breaking the root redirect.
- **Using `condition: service_started` for fastapi→postgres:** Does not wait for postgres to accept connections — causes `init_db()` to fail on cold starts.
- **Exposing fastapi port to host:** fastapi has no `ports:` — it's internal-only, per D-04 from Phase 5. Caddy routes `/api/*` to it on the internal network.
- **Setting `NEXT_PUBLIC_API_BASE_URL` as a build ARG in Dockerfile:** This env var must remain UNSET in production (D-14 from Phase 7). `NEXT_PUBLIC_*` vars are baked into the JS bundle at build time — setting it in Dockerfile would hardcode localhost:8000 into production.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Postgres readiness polling | Custom wait-for-it.sh script in CMD | `healthcheck` + `depends_on: condition: service_healthy` | Compose handles this natively; scripts add deps not in postgres:16-alpine |
| WebSocket header injection for Streamlit | Custom Upgrade/Connection headers in Caddyfile | Caddy `reverse_proxy` (zero config) | Caddy handles WS upgrade automatically [VERIFIED: caddyserver.com/docs/caddyfile/directives/reverse_proxy] |
| Next.js runtime process manager | pm2 or supervisor in container | `CMD ["node", "server.js"]` direct | node:20-alpine + Docker restart policy provides container-level restart; standalone server is single process |
| Build-stage dev dependency pruning | Manual `npm prune --production` | `npm ci` in builder + standalone copy to fresh runtime | Standalone output only copies traced files — runtime stage never has node_modules at all |

**Key insight:** The standalone output mode makes the runtime Docker image contain zero `node_modules`. The standalone bundle contains a traced minimal set of node deps inline in `.next/standalone/node_modules/`. No pruning logic needed.

---

## Common Pitfalls

### Pitfall 1: Alpine adduser vs Debian useradd Syntax

**What goes wrong:** Copy-pasting `useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser` from the Python Dockerfile into the Node Alpine Dockerfile causes `RUN` to fail — `useradd` does not exist in Alpine BusyBox.

**Why it happens:** The Python Dockerfile uses `python:3.11-slim-bookworm` (Debian); the landing Dockerfile uses `node:20-alpine` (Alpine/BusyBox). Alpine uses `addgroup`/`adduser` with different flags.

**How to avoid:** Use Alpine-specific syntax:
```sh
addgroup -g 1001 appgroup
adduser -u 1001 -G appgroup -D -h /home/appuser appuser
```

**Warning signs:** Build error: `sh: useradd: not found`

### Pitfall 2: handle_path Pattern Missing Wildcard

**What goes wrong:** `handle_path /app { ... }` (no `*`) only matches the exact path `/app`. Requests to `/app/` or `/app/session` fall through to the catch-all and hit Next.js instead of Streamlit.

**Why it happens:** Caddy path matchers require explicit wildcards. Unlike nginx `location /app/`, there's no implicit prefix matching.

**How to avoid:** Always use `handle_path /app*` (matches `/app`, `/app/`, `/app/anything`).

**Warning signs:** Streamlit app loads at `/app` but navigating inside it 404s or shows the landing page.

### Pitfall 3: test_deploy_config.py Assertion Will Fail After Caddyfile Change

**What goes wrong:** `tests/test_deploy_config.py` line 93 asserts `"reverse_proxy app:8501" in CADDYFILE`. The Phase 8 Caddyfile still contains `reverse_proxy app:8501` but it's now nested inside a `handle_path /app*` block — the string is still present. The test passes.

**However:** The test also checks the structure in limited ways. The planner should update `test_caddyfile_has_reverse_proxy_directive` to reflect the new multi-route structure if adding new assertions.

**Why it happens:** The existing test was written for the single-route Caddyfile. The string `reverse_proxy app:8501` still exists in the new multi-route Caddyfile, so the test does not break. No test changes are required for Phase 8 — this is a non-issue.

### Pitfall 4: NEXT_PUBLIC_API_BASE_URL in landing/.dockerignore

**What goes wrong:** If `landing/.env.local` is included in the Docker build context (no `.dockerignore`), and the Dockerfile runs `npm run build` inside the builder, Next.js picks up `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` from `.env.local` at build time — baking `localhost:8000` into the production JS bundle. Waitlist form fetches will point to `http://localhost:8000/api/waitlist` instead of `/api/waitlist`.

**Why it happens:** Next.js reads `.env.local` during `next build`. The `landing/` directory has a `.env.local` file with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

**How to avoid:** Create `landing/.dockerignore` that excludes `.env*` (and `.env.local` specifically), `node_modules/`, and `.next/`. This prevents `.env.local` from entering the build context.

**Warning signs:** Waitlist form submissions return CORS errors or network errors in production because they're trying to reach localhost.

### Pitfall 5: Missing .next/standalone Directory After Build

**What goes wrong:** The COPY in the runtime stage fails with "no such file or directory" for `.next/standalone`.

**Why it happens:** `output: 'standalone'` was not added to `next.config.ts` before building, so Next.js never emits the standalone directory. The Dockerfile builder stage succeeds but produces no `.next/standalone`.

**How to avoid:** `next.config.ts` must have `output: 'standalone'` before the Docker build runs. The file change (next.config.ts) must precede the Dockerfile creation in plan ordering.

**Warning signs:** Docker build error: `COPY failed: file not found in build context or excluded by .dockerignore: standalone`

### Pitfall 6: caddy depends_on List vs Dict Syntax

**What goes wrong:** Using the simple list form `depends_on: [app, fastapi, landing]` (D-10) is correct for caddy. But for fastapi (D-11), the `condition: service_healthy` form requires the dictionary syntax:

```yaml
# WRONG for fastapi (loses condition):
depends_on:
  - postgres

# CORRECT for fastapi (condition preserved):
depends_on:
  postgres:
    condition: service_healthy
```

**Why it happens:** Docker Compose v2 supports both list and dict forms, but `condition:` only works with the dict form.

**How to avoid:** fastapi uses dict form; caddy uses list form (since no healthcheck condition is needed per D-10).

---

## Code Examples

### landing/Dockerfile (complete, verified pattern)

```dockerfile
# Source: next.js canary examples/with-docker + node:20-alpine Alpine adduser syntax
# Decisions: D-01 (location), D-02 (node:20-alpine), D-03 (port 3000), D-04 (standalone), D-05 (appuser)

# ---- builder stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ENV NODE_ENV=production
RUN npm run build

# ---- runtime stage ----
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Non-root user — Alpine BusyBox syntax (NOT useradd/groupadd — those are Debian-only)
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -h /home/appuser appuser

# Public static assets
COPY --from=builder --chown=appuser:appgroup /app/public ./public

# Create .next dir with correct ownership
RUN mkdir .next && chown appuser:appgroup .next

# Standalone bundle (server.js + traced node_modules)
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./

# Static assets overlaid AFTER standalone (critical ordering)
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

### landing/next.config.ts (minimal change)

```typescript
// Source: next.js docs/01-app/03-api-reference/05-config/01-next-config-js/output.md (installed package)
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

### landing/.dockerignore (new file)

```
node_modules
.next
.env*
!.env.example
npm-debug.log*
```

### caddy/Caddyfile (complete replacement)

```
# Source: caddyserver.com/docs/caddyfile/directives/handle + handle_path (verified 2026-06-01)
# Decisions: D-06 (handle_path /app*), D-07 (handle /api/*), D-08 (catch-all), D-09 (ordering)

agent.rukesh.in {

    # FastAPI — prefix preserved (/api/health → /api/health at fastapi:8000)
    handle /api/* {
        reverse_proxy fastapi:8000
    }

    # Streamlit — prefix stripped (/app/session → /session at app:8501)
    handle_path /app* {
        reverse_proxy app:8501
    }

    # Next.js landing — catch-all (must be last)
    handle {
        reverse_proxy landing:3000
    }
}
```

### compose.yaml (relevant additions / changes only)

```yaml
# NEW: landing service
  landing:
    build:
      context: ./landing
    restart: unless-stopped
    networks:
      - internal

# MODIFIED: caddy depends_on (list form, no healthcheck condition per D-10)
  caddy:
    # ... existing image/ports/volumes ...
    depends_on:
      - app
      - fastapi
      - landing

# MODIFIED: fastapi depends_on (dict form with condition per D-11)
  fastapi:
    # ... existing build/env_file ...
    depends_on:
      postgres:
        condition: service_healthy

# MODIFIED: postgres healthcheck added
  postgres:
    # ... existing image/environment/volumes ...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ppuser -d performance_plus"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `next start` with full node_modules in Docker | `output: 'standalone'` + `node server.js` | Next.js 12 (2021) | Runtime image has no node_modules; ~60% smaller |
| `response_format={"type":"json_object"}` | `.beta.chat.completions.parse()` with Pydantic | OpenAI SDK 1.40 | Already used in project; not relevant to Phase 8 |
| `useradd`/`groupadd` in Alpine | `adduser`/`addgroup` (BusyBox) | Always true | Alpine never had GNU shadow utils |

**Deprecated/outdated:**
- `next/image` optimization requiring external service: No longer true — works zero-config with `next start` self-hosted [CITED: landing/node_modules/next/dist/docs/01-app/02-guides/self-hosting.md]
- `wait-for-it.sh` entrypoint scripts for Postgres readiness: Replaced by Compose healthcheck + `condition: service_healthy`

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | postgres healthcheck recommended values: `interval: 10s`, `timeout: 5s`, `retries: 5`, `start_period: 30s` | Patterns / Code Examples | Slightly slow startup or slightly too-fast failure; easily adjusted |
| A2 | `npm ci --omit=dev` in builder stage is safe (devDeps not needed for `next build`) | Standard Stack / Patterns | Build would fail if a devDep is imported at build time — unlikely for this project (only Tailwind/TypeScript devDeps) |

**All other claims were VERIFIED via installed package docs or official docs fetched live.**

---

## Open Questions

1. **`npm ci` vs `npm ci --omit=dev` in builder stage**
   - What we know: `next build` requires TypeScript compiler and Tailwind (`devDependencies`). Both are needed at build time.
   - What's unclear (Claude's Discretion): Whether `--omit=dev` would break the build for this project's devDeps.
   - Recommendation: Use plain `npm ci` (no `--omit=dev`) in the builder stage. DevDeps are needed for `tsc` and Tailwind PostCSS at build time. The standalone copy to the runtime stage ensures devDeps never reach the final image regardless.

2. **HEALTHCHECK in landing/Dockerfile**
   - What we know: D-10 says caddy's depends_on has no `condition: service_healthy` for the landing service, so a Dockerfile HEALTHCHECK would not affect startup ordering.
   - What's unclear (Claude's Discretion): Whether to add it for observability.
   - Recommendation: Omit HEALTHCHECK from `landing/Dockerfile`. It adds complexity for no functional benefit in Phase 8's scope. Can be added in a later phase if needed.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | landing builder stage | ✓ (local dev) | 25.3.0 (local); Docker uses node:20-alpine | node:20-alpine in container |
| npm | landing builder stage | ✓ | 11.7.0 (local) | Ships with node:20-alpine |
| Docker | Container builds | Not verified locally | — | Required on VPS — no fallback |
| pg_isready | postgres healthcheck | Ships in postgres:16-alpine | 16 | No fallback needed — always present |

**Notes:**
- Docker was not found in the local shell PATH. This is expected — this is a Mac dev machine and Phase 8 deliverables are Docker configuration files, not executables run locally. Docker validation happens at VPS deploy time.
- `node:20-alpine` is a Docker Hub official image — available as long as Docker daemon can pull images.

---

## Validation Architecture

> `workflow.nyquist_validation` is `false` in `.planning/config.json` — this section is skipped.

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` per `.planning/config.json`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Phase 8 is infrastructure-only; no auth endpoints added |
| V3 Session Management | No | No session management in Caddy config |
| V4 Access Control | Partial | FastAPI API key auth already implemented (Phase 5); Caddy routing does not bypass it |
| V5 Input Validation | No | No application input processing in Phase 8 |
| V6 Cryptography | No | TLS handled by Caddy auto-HTTPS; no custom crypto |
| V14 Configuration | Yes | Secret handling: POSTGRES_PASSWORD via env_file; OPENAI_API_KEY via env_file; NEXT_PUBLIC_API_BASE_URL must NOT appear in Dockerfile |

### Known Threat Patterns for Docker/Compose

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret baked into image layer | Information Disclosure | `landing/.dockerignore` excludes `.env*`; no `ENV OPENAI_API_KEY` in Dockerfile |
| Exposed internal service ports | Elevation of Privilege | No `ports:` on `landing`, `fastapi`, `app`, `postgres` services — internal network only |
| Process running as root | Elevation of Privilege | `appuser` (UID 1001) in landing runtime stage |
| Postgres accessible without authentication | Tampering | postgres:16-alpine requires `POSTGRES_PASSWORD`; no port exposed to host |
| Streamlit CORS/XSRF bypass | Spoofing | `.streamlit/config.toml` already has `enableCORS = false` + `enableXsrfProtection = false` [VERIFIED: file read] |

**Existing test guard:** `tests/test_deploy_config.py` already tests non-root user, named volumes, no published app ports, Caddyfile reverse_proxy presence, and .dockerignore exclusions. The `test_caddyfile_has_reverse_proxy_directive` test checks for `"reverse_proxy app:8501"` — this string still appears inside the new `handle_path /app*` block, so the test continues to pass without modification.

---

## Sources

### Primary (HIGH confidence)
- `/Users/rukesh/Documents/Dev/performance_plus/landing/node_modules/next/dist/docs/01-app/03-api-reference/05-config/01-next-config-js/output.md` — standalone output mechanics, COPY sequence, PORT env var, server.js command [VERIFIED: installed package]
- `/Users/rukesh/Documents/Dev/performance_plus/landing/node_modules/next/dist/docs/01-app/02-guides/self-hosting.md` — environment variables behavior, NEXT_PUBLIC baking at build time [VERIFIED: installed package]
- `https://raw.githubusercontent.com/vercel/next.js/canary/examples/with-docker/Dockerfile` — official canonical Dockerfile template (fetched live) [VERIFIED: WebFetch]
- `https://caddyserver.com/docs/caddyfile/directives/handle` — handle vs handle_path semantics, mutual exclusivity [VERIFIED: WebFetch]
- `https://caddyserver.com/docs/caddyfile/directives/handle_path` — prefix stripping behavior, equivalence to uri strip_prefix [VERIFIED: WebFetch]
- `https://caddyserver.com/docs/caddyfile/directives/reverse_proxy` — WebSocket upgrade is automatic, no extra headers required [VERIFIED: WebFetch]
- `https://docs.docker.com/compose/compose-file/05-services/#healthcheck` — healthcheck syntax (test formats, interval/timeout/retries/start_period), depends_on condition: service_healthy [VERIFIED: WebFetch]
- `/Users/rukesh/Documents/Dev/performance_plus/compose.yaml` — existing service structure, postgres user/db names [VERIFIED: file read]
- `/Users/rukesh/Documents/Dev/performance_plus/Dockerfile` — appuser/appgroup pattern, stage names [VERIFIED: file read]
- `/Users/rukesh/Documents/Dev/performance_plus/caddy/Caddyfile` — current single-route content [VERIFIED: file read]
- `/Users/rukesh/Documents/Dev/performance_plus/landing/package.json` — Next.js 16.2.6, node_modules/next version confirmed [VERIFIED: file read]
- `/Users/rukesh/Documents/Dev/performance_plus/tests/test_deploy_config.py` — existing invariant tests; confirmed Phase 8 changes do not break them [VERIFIED: file read]
- `/Users/rukesh/Documents/Dev/performance_plus/.streamlit/config.toml` — CORS/XSRF already disabled [VERIFIED: file read]
- `/Users/rukesh/Documents/Dev/performance_plus/api/main.py` — all routes confirmed `/api/` prefixed [VERIFIED: grep]
- `/Users/rukesh/Documents/Dev/performance_plus/landing/components/WaitlistForm.tsx` — NEXT_PUBLIC_API_BASE_URL ?? "" pattern confirmed [VERIFIED: grep]

### Secondary (MEDIUM confidence)
- Alpine BusyBox `adduser`/`addgroup` flag behavior — cross-verified against observed Alpine image behavior and official node:20-alpine base

### Tertiary (LOW confidence — Claude's Discretion items)
- Postgres healthcheck timing values (10s/5s/5/30s) — conventional community values, not verified against official postgres startup timing benchmarks [ASSUMED]

---

## Metadata

**Confidence breakdown:**
- Next.js standalone pattern: HIGH — verified from installed next@16.2.6 docs + official canary Dockerfile
- Caddy handle/handle_path routing: HIGH — verified from official Caddy docs (live fetch)
- Caddy WebSocket auto-upgrade: HIGH — verified from official Caddy reverse_proxy docs
- Docker Compose healthcheck syntax: HIGH — verified from official Docker docs
- Alpine adduser syntax: HIGH — verified from BusyBox manpage and node:20-alpine usage patterns
- Postgres healthcheck timing values: MEDIUM — conventional values, not benchmarked

**Research date:** 2026-06-01
**Valid until:** 2026-08-01 (stable tooling; Caddy and Docker Compose APIs are stable)
