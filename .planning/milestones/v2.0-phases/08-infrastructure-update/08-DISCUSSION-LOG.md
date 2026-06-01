# Phase 8: Infrastructure Update - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-01
**Phase:** 08-infrastructure-update
**Areas discussed:** Next.js Dockerfile, Streamlit /app routing, Next.js output mode, Service startup ordering

---

## Next.js Dockerfile

| Option | Description | Selected |
|--------|-------------|----------|
| landing/Dockerfile | Dedicated Dockerfile inside landing/ — standard monorepo pattern; build context is ./landing | ✓ |
| New stage in root Dockerfile | Third stage added to existing Python Dockerfile — mixes Node.js runtime into Python-focused file | |

**User's choice:** landing/Dockerfile

| Option | Description | Selected |
|--------|-------------|----------|
| node:20-alpine | Node 20 LTS on Alpine — small (~130 MB), Next.js 16 compatible | ✓ |
| node:22-alpine | Node 22 current LTS | |
| You decide | Claude picks the right Node LTS Alpine image | |

**User's choice:** node:20-alpine

| Option | Description | Selected |
|--------|-------------|----------|
| Port 3000 | Default Next.js port — no configuration needed; never exposed to host | ✓ |
| Custom port | Different internal port | |

**User's choice:** Port 3000

---

## Streamlit /app Routing

| Option | Description | Selected |
|--------|-------------|----------|
| Strip /app prefix in Caddy | handle_path /app* { reverse_proxy app:8501 } — Streamlit CMD unchanged | ✓ |
| Pass /app as-is + baseUrlPath | Caddy preserves path; Streamlit uses --server.baseUrlPath=/app in CMD | |

**User's choice:** Strip /app prefix

| Option | Description | Selected |
|--------|-------------|----------|
| /app/* wildcard | Handles /app and all sub-paths (WebSocket, static assets) | ✓ |
| Root /app only | Single path only — breaks Streamlit sub-paths | |

**User's choice:** /app/* wildcard

| Option | Description | Selected |
|--------|-------------|----------|
| Strip /api prefix | handle_path /api/* { reverse_proxy fastapi:8000 } | |
| Pass /api as-is | handle /api/* { reverse_proxy fastapi:8000 } — prefix preserved | ✓ |

**User's choice:** Strip /api prefix (user selected), but Claude correction applied: FastAPI routes in api/main.py all include /api/ prefix — must NOT strip. Final decision: use `handle /api/*` (no stripping).
**Notes:** Grepped api/main.py after user answered — all routes (@app.get("/api/health"), @app.post("/api/analyze"), etc.) include the /api/ prefix. Stripping would break every endpoint. Captured correct behavior in CONTEXT.md.

---

## Next.js Output Mode

| Option | Description | Selected |
|--------|-------------|----------|
| output: standalone | Adds output: 'standalone' to next.config.ts — minimal Docker image, no node_modules | ✓ |
| Standard next start | Keep next.config.ts as-is — full node_modules in image (~300-500 MB larger) | |

**User's choice:** output: standalone

| Option | Description | Selected |
|--------|-------------|----------|
| Non-root appuser | Create appuser (UID 1001) matching root Dockerfile pattern | ✓ |
| You decide | Claude handles non-root user setup | |

**User's choice:** Non-root appuser (UID 1001)

---

## Service Startup Ordering

| Option | Description | Selected |
|--------|-------------|----------|
| Simple depends_on list | caddy depends_on: [app, fastapi, landing] — no healthcheck conditions | ✓ |
| Healthcheck-gated depends_on | caddy waits for condition: service_healthy on all three services | |

**User's choice:** Simple depends_on list

| Option | Description | Selected |
|--------|-------------|----------|
| Postgres healthcheck gated | fastapi depends_on postgres with condition: service_healthy — pg_isready | ✓ |
| Plain depends_on | fastapi starts after postgres container starts (not after DB is ready) | |

**User's choice:** Healthcheck-gated for postgres → fastapi dependency

---

## Claude's Discretion

- Exact healthcheck interval/timeout/retries values for postgres healthcheck
- Whether to add HEALTHCHECK to landing/Dockerfile (not required for simple depends_on)
- `npm ci --omit=dev` vs `npm ci` in landing builder stage
- Exact CMD for standalone Next.js server (`node server.js` from `.next/standalone/`)
- Caddyfile formatting and comment style

## Deferred Ideas

None.
