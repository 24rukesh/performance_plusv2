---
phase: 08-infrastructure-update
plan: "03"
subsystem: infrastructure
tags:
  - caddy
  - reverse-proxy
  - routing
  - websocket
dependency_graph:
  requires:
    - 08-01 (landing/Dockerfile, next.config.ts standalone — services referenced by Caddyfile)
    - 08-02 (compose.yaml landing service, caddy depends_on — service names used as upstream hostnames)
  provides:
    - Multi-route Caddy reverse proxy: /api/* → fastapi:8000, /app* → app:8501, / → landing:3000
    - Unified TLS-terminated domain (agent.rukesh.in) routing all three services
  affects:
    - caddy container routing behaviour (runtime — requires docker compose up caddy)
tech_stack:
  added: []
  patterns:
    - "Caddy handle vs handle_path: handle preserves prefix (API), handle_path strips prefix (Streamlit)"
    - "Caddy catch-all handle block must be last (D-09: most-specific-first document order)"
    - "Caddy reverse_proxy handles WebSocket upgrade automatically — no Upgrade/Connection headers needed"
key_files:
  created: []
  modified:
    - caddy/Caddyfile
decisions:
  - "handle /api/* (not handle_path) preserves /api/ prefix — all FastAPI routes include it; stripping would 404 every route (D-07)"
  - "handle_path /app* (not /app/*) — /app* glob matches bare /app and /app/anything; /app/* would miss bare /app (Pitfall 2, D-06)"
  - "catch-all handle placed last — Caddy first-match-wins evaluation order (D-09)"
  - "No explicit Upgrade/Connection headers — Caddy reverse_proxy auto-upgrades WebSocket (prevents #1 Streamlit self-hosted proxy bug)"
metrics:
  duration: "~2 min"
  completed: "2026-06-01"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
---

# Phase 8 Plan 03: Caddyfile Multi-Route Routing Summary

**One-liner:** Three-route Caddy site block routing /api/* to FastAPI (prefix preserved), /app* to Streamlit (prefix stripped), and catch-all to Next.js landing page behind a single TLS domain.

## What Was Built

Replaced the single-route `caddy/Caddyfile` (`agent.rukesh.in { reverse_proxy app:8501 }`) with a three-handler site block that unifies all three application services behind `agent.rukesh.in`.

### Route Table (document order — first match wins)

| Order | Directive | Matcher | Upstream | Prefix Behavior |
|-------|-----------|---------|----------|-----------------|
| 1 | `handle` | `/api/*` | `fastapi:8000` | Preserved — FastAPI expects `/api/health`, not `/health` (D-07) |
| 2 | `handle_path` | `/app*` | `app:8501` | Stripped — Streamlit serves at `/`; `/app/session` → `/session` (D-06) |
| 3 | `handle` | (catch-all) | `landing:3000` | N/A — Next.js receives path as-is (D-08) |

## Files Modified

### caddy/Caddyfile

Complete replacement — 3 lines → 16 lines.

Key structural properties verified:
- `handle /api/*` appears before `handle_path /app*` which appears before `reverse_proxy landing:3000` (D-09 document-order enforced)
- Glob is `/app*` (no slash after `app`) — matches `/app`, `/app/`, `/app/anything` (Pitfall 2 avoided)
- No `handle_path /app/*` substring present (Pitfall 2 check)
- No `Upgrade`, `Connection`, `admin off`, or `admin :` strings present

## Verification Results

### Static Structural Checks (all passed)

| Check | Result |
|-------|--------|
| `^agent\.rukesh\.in {` first non-empty line | PASS |
| `handle /api/*` present | PASS |
| `handle_path /app*` present | PASS |
| `handle_path /app/*` absent (Pitfall 2) | PASS |
| `reverse_proxy fastapi:8000` present | PASS |
| `reverse_proxy app:8501` present | PASS |
| `reverse_proxy landing:3000` present | PASS |
| Route order: api(100) < app(234) < landing(362) char positions | PASS |
| `Upgrade` absent | PASS |
| `Connection` absent | PASS |
| `admin` directive absent | PASS |

### Test Suite

- `uv run pytest tests/test_deploy_config.py::test_caddyfile_has_reverse_proxy_directive -q` — **1 passed** (substring `reverse_proxy app:8501` still present inside `handle_path /app*` block per Pitfall 3 analysis)
- `uv run pytest -q` — **81 passed, 5 skipped** (no regressions; no Python files modified)

### Deferred to VPS Deploy-Time

Docker/Caddy not available locally. The following require `docker compose up caddy` on the VPS:
- `caddy validate --config /etc/caddy/Caddyfile` inside the container
- HTTPS reachability: `/` → Next.js HTML; `/api/health` → `{"status":"ok"}`; `/app/` → Streamlit with established WebSocket

## Threat Mitigations Applied

| Threat ID | Mitigation Applied |
|-----------|-------------------|
| T-08-11 | `handle /api/*` (not `handle_path`) — prefix preserved; FastAPI routes cannot be 404'd by stripping |
| T-08-12 | `handle_path /app*` (not `/app/*`) — glob covers bare `/app`; no silent fall-through to catch-all |
| T-08-15 | No `admin off` or `admin :` directive — Caddy admin API stays on default 127.0.0.1:2019 |
| T-08-16 | Document order enforced: /api/* (line 4) before /app* (line 9) before landing (line 14) |

## Deviations from Plan

None — plan executed exactly as written.

## End-of-Phase Note

Phase 8 ships pure infrastructure (Plans 01–03). No application behavior has changed. The three services (Next.js landing, FastAPI, Streamlit) were already containerised and orchestrated in Plans 01–02. Plan 03 activates the routing layer that makes them reachable from a single domain.

The next user-visible change requires `docker compose up -d` (or `docker compose pull && docker compose up -d`) on the VPS. After that:
- `https://agent.rukesh.in/` → Next.js landing page
- `https://agent.rukesh.in/api/health` → FastAPI JSON
- `https://agent.rukesh.in/app/` → Streamlit app with WebSocket

Phase 8 is now complete (3/3 plans).

## Self-Check: PASSED

- caddy/Caddyfile: FOUND
- 08-03-SUMMARY.md: FOUND
- Commit cf5f7fe: FOUND
