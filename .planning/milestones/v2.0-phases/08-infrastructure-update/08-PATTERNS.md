# Phase 8: Infrastructure Update - Pattern Map

**Mapped:** 2026-06-01
**Files analyzed:** 5 (3 new, 2 modified)
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `landing/Dockerfile` | config (container) | build-artifact | `./Dockerfile` (multi-stage Python build) | role-match (same multi-stage pattern; different base OS requires Alpine adduser syntax) |
| `landing/.dockerignore` | config | file-I/O | `./.dockerignore` (root Python dockerignore) | role-match (same purpose; different exclusion set) |
| `landing/next.config.ts` | config | transform | existing file (empty config) | exact (in-place addition of one key) |
| `compose.yaml` | config (orchestration) | event-driven | existing file (current compose.yaml) | exact (in-place modification) |
| `caddy/Caddyfile` | config (routing) | request-response | existing file (current single-route Caddyfile) | exact (in-place replacement) |

---

## Pattern Assignments

### `landing/Dockerfile` (config, build-artifact)

**Analog:** `./Dockerfile`

**Non-root user — Debian pattern in analog** (`./Dockerfile` lines 31-32 and lines 56-57):
```dockerfile
# Debian/slim-bookworm syntax used in ./Dockerfile (streamlit stage, lines 31-32):
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser

# Debian/slim-bookworm syntax used in ./Dockerfile (api stage, lines 56-57):
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser
```

**CRITICAL DIFFERENCE — Alpine syntax for `landing/Dockerfile`:**
`node:20-alpine` uses BusyBox; `useradd`/`groupadd` do not exist. The equivalent Alpine commands are:
```dockerfile
# Alpine/BusyBox syntax — use this in landing/Dockerfile (NOT the Debian version above):
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -h /home/appuser appuser
# Flag mapping:
#   addgroup -g 1001 appgroup      → groupadd -g 1001 appgroup
#   adduser -u 1001                → useradd -u 1001
#   adduser -G appgroup            → useradd -g appgroup  (capital -G on Alpine = primary group)
#   adduser -D                     → no password (system user equivalent; replaces -s /bin/false)
#   adduser -h /home/appuser       → useradd -m -d /home/appuser (home created automatically on Alpine when -h set)
```

**COPY ownership pattern from analog** (`./Dockerfile` line 37):
```dockerfile
COPY --from=builder --chown=appuser:appgroup /app /app
```
Same `--chown=appuser:appgroup` flag applies to all COPY instructions in `landing/Dockerfile`.

**Multi-stage build structure from analog** (`./Dockerfile` lines 3-4, 27-28, 52-53):
```dockerfile
# Stage naming convention used in ./Dockerfile:
FROM python:3.11-slim-bookworm AS builder
FROM python:3.11-slim-bookworm AS streamlit
FROM python:3.11-slim-bookworm AS api

# Landing Dockerfile follows same AS-naming convention:
FROM node:20-alpine AS builder
FROM node:20-alpine AS runner
```

**WORKDIR pattern from analog** (`./Dockerfile` lines 12, 34, 59):
```dockerfile
WORKDIR /app
```
Same `/app` WORKDIR used in all stages of `landing/Dockerfile`.

**EXPOSE + USER pattern from analog** (`./Dockerfile` lines 43-45, 68-70):
```dockerfile
USER appuser
EXPOSE 8501   # → landing/Dockerfile uses EXPOSE 3000
```

**Complete `landing/Dockerfile` — assembled from analog structure + Alpine syntax + standalone copy sequence:**
```dockerfile
# syntax=docker/dockerfile:1.7

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
# GID/UID 1001 consistent with ./Dockerfile appgroup/appuser pattern (D-05)
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -h /home/appuser appuser

# 1. Public static assets
COPY --from=builder --chown=appuser:appgroup /app/public ./public

# 2. Create .next dir with correct ownership before standalone copy
RUN mkdir .next && chown appuser:appgroup .next

# 3. Standalone bundle (server.js + traced node_modules)
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./

# 4. Static assets overlaid AFTER standalone (critical — must be last)
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

**COPY order note (anti-pattern to avoid):** Static assets (`4.`) must come AFTER the standalone copy (`3.`). Reversing the order causes static files to be overwritten by the standalone bundle.

---

### `landing/.dockerignore` (config, file-I/O)

**Analog:** `./.dockerignore`

**Root `.dockerignore` pattern** (`./.dockerignore` full file):
```
.venv/
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.ruff_cache/
tests/
*.md
design/
.planning/
.git/
.DS_Store
```

**`landing/.dockerignore` — adapted for Node.js + critical .env exclusion:**
The root analog excludes `.env` as a single file. The landing version must use `.env*` glob (not `.env`) to also exclude `.env.local` — which contains `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`. If `.env.local` enters the build context, `npm run build` bakes `localhost:8000` into the production JS bundle, breaking the waitlist form in production.

```
node_modules
.next
.env*
!.env.example
npm-debug.log*
.DS_Store
```

**Key difference from root analog:**
- Root uses `.env` (exact filename match) — fine for Python, which reads .env at runtime via python-dotenv
- Landing uses `.env*` glob — required because Next.js reads `.env.local` at **build time** (bakes NEXT_PUBLIC_ vars into JS bundle)

---

### `landing/next.config.ts` (config, transform)

**Analog:** existing `landing/next.config.ts` (the file being modified)

**Current state** (`landing/next.config.ts` lines 1-7):
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
```

**Modified state — add `output: 'standalone'`:**
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

**Change:** Replace `/* config options here */` comment with `output: "standalone"`. No other changes. This single key triggers Next.js to emit `.next/standalone/server.js` during `npm run build`, which is what `landing/Dockerfile` copies. Without this key, the Dockerfile COPY for `.next/standalone` will fail at build time.

---

### `compose.yaml` (config, event-driven orchestration)

**Analog:** existing `compose.yaml` (the file being modified)

**Current `app` service block — pattern to replicate for `landing`** (`compose.yaml` lines 2-9):
```yaml
  app:
    build:
      context: .
      target: streamlit
    restart: unless-stopped
    env_file: .env
    networks:
      - internal
```

**`landing` service — adapted from `app` pattern:**
```yaml
  landing:
    build:
      context: ./landing
    restart: unless-stopped
    networks:
      - internal
```
Differences from `app`: `context: ./landing` (not `.`); no `target:` (landing/Dockerfile has only one output stage named `runner` — no multi-target); no `env_file:` (no server-side secrets; NEXT_PUBLIC_ vars are baked at build time, not runtime).

**Current `caddy` depends_on — line to replace** (`compose.yaml` lines 24-25):
```yaml
    depends_on:
      - app
```

**Updated `caddy` depends_on — simple list form (D-10, no healthcheck condition):**
```yaml
    depends_on:
      - app
      - fastapi
      - landing
```

**Current `fastapi` depends_on — lines to replace** (`compose.yaml` lines 34-36):
```yaml
    depends_on:
      - postgres
```

**Updated `fastapi` depends_on — dict form with condition (D-11):**
```yaml
    depends_on:
      postgres:
        condition: service_healthy
```

**Current `postgres` service — lines 38-48 (no healthcheck):**
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
```

**Updated `postgres` service — add healthcheck block after `networks:`:**
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

**`depends_on` form note (Pitfall 6):** `caddy` uses simple list form (no condition needed per D-10). `fastapi` MUST use dict form — the `condition: service_healthy` key is only valid in dict form. Using list form for fastapi silently drops the condition and causes the init_db() startup race.

---

### `caddy/Caddyfile` (config, request-response routing)

**Analog:** existing `caddy/Caddyfile` (the file being replaced)

**Current state** (`caddy/Caddyfile` lines 1-3):
```
agent.rukesh.in {
    reverse_proxy app:8501
}
```

**Complete replacement:**
```
agent.rukesh.in {

    # FastAPI — prefix preserved (/api/health stays /api/health at fastapi:8000)
    handle /api/* {
        reverse_proxy fastapi:8000
    }

    # Streamlit — prefix stripped (/app/session → /session at app:8501)
    # handle_path strips /app before proxying; Streamlit sees requests at /
    handle_path /app* {
        reverse_proxy app:8501
    }

    # Next.js landing page — catch-all (must be last)
    handle {
        reverse_proxy landing:3000
    }
}
```

**Route ordering rationale (D-09):** More specific matchers first. Caddy evaluates `handle` blocks in document order; catch-all `handle {}` at bottom is last resort.

**`handle` vs `handle_path` semantics:**
- `handle /api/*` — preserves prefix. `/api/health` arrives at FastAPI as `/api/health`. Required because all FastAPI routes are prefixed with `/api/`.
- `handle_path /app*` — strips matched prefix. `/app/session` arrives at Streamlit as `/session`. The pattern is `/app*` (no slash after `app`) — this matches `/app`, `/app/`, and `/app/anything`. Using `/app/*` would miss requests to `/app` itself.
- `handle {}` — catch-all, no matcher argument. Matches everything not caught above.

**WebSocket note:** Caddy's `reverse_proxy` automatically handles WebSocket upgrade — no `Upgrade`/`Connection` headers required. This is why Streamlit works behind Caddy with no extra config (the #1 self-hosted Streamlit footgun is Nginx default config dropping the WS upgrade).

---

## Shared Patterns

### Non-Root User Creation (Security)
**Source:** `./Dockerfile` lines 31-32 (streamlit stage) and 56-57 (api stage)
**Apply to:** `landing/Dockerfile` runtime stage
**Pattern:** GID/UID 1001, group name `appgroup`, user name `appuser`, `/home/appuser` home dir.

Debian (existing Dockerfile — DO NOT copy to Alpine):
```dockerfile
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser
```

Alpine equivalent (use this in `landing/Dockerfile`):
```dockerfile
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -h /home/appuser appuser
```

### COPY Ownership
**Source:** `./Dockerfile` line 37
**Apply to:** All COPY instructions in `landing/Dockerfile` runtime stage
```dockerfile
COPY --from=builder --chown=appuser:appgroup <src> <dest>
```

### Restart Policy
**Source:** `compose.yaml` lines 7, 15, 31 (`restart: unless-stopped`)
**Apply to:** `landing` service in `compose.yaml`
```yaml
restart: unless-stopped
```

### Internal Network Only (No Exposed Ports)
**Source:** `compose.yaml` — `app`, `fastapi`, `postgres` services have no `ports:` key
**Apply to:** `landing` service — must NOT have `ports:` (only `caddy` publishes 80/443)

### `dockerfile:1.7` Syntax Directive
**Source:** `./Dockerfile` line 1
**Apply to:** `landing/Dockerfile` line 1
```dockerfile
# syntax=docker/dockerfile:1.7
```

---

## No Analog Found

All files in scope have close analogs. No files require fallback to RESEARCH.md-only patterns.

---

## Metadata

**Analog search scope:** `/Users/rukesh/Documents/Dev/performance_plus/` (root Dockerfile, compose.yaml, caddy/Caddyfile, landing/next.config.ts, .dockerignore)
**Files scanned:** 5 analog files read in full
**Pattern extraction date:** 2026-06-01
