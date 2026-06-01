---
phase: 08-infrastructure-update
plan: 02
subsystem: infra
tags: [docker-compose, postgres, healthcheck, orchestration, landing, caddy]

# Dependency graph
requires:
  - phase: 08-infrastructure-update
    plan: 01
    provides: "landing/Dockerfile at ./landing/Dockerfile — required for build: context: ./landing reference"
provides:
  - "compose.yaml with four-service orchestration: app + fastapi + landing + postgres + caddy"
  - "postgres healthcheck using pg_isready eliminating FastAPI init_db() startup race"
  - "landing service block with internal-only network, no ports, no env_file"
  - "caddy depends_on [app, fastapi, landing] list form (D-10)"
  - "fastapi depends_on postgres with condition: service_healthy dict form (D-11)"
affects:
  - "08-03 (Caddyfile multi-route config — landing service now declared in compose)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Docker Compose healthcheck: pg_isready -U ppuser -d performance_plus with interval/timeout/retries/start_period"
    - "depends_on dict form with condition: service_healthy for health-gated startup ordering"
    - "depends_on list form (no condition) for simple startup sequencing (caddy after app/fastapi/landing)"
    - "landing service: build.context ./landing, no ports, no env_file, internal network only"

key-files:
  created: []
  modified:
    - "compose.yaml"

key-decisions:
  - "Postgres healthcheck values: interval 10s, timeout 5s, retries 5, start_period 30s — conventional community values per RESEARCH.md A1 (Claude's Discretion area)"
  - "caddy depends_on uses list form (not dict form with condition) per D-10 — no health-gating on caddy startup, restart: unless-stopped provides recovery"
  - "landing service has no env_file key — NEXT_PUBLIC_* vars baked at build time, no server-side secrets per D-14/T-08-07"
  - "landing service has no target key in build — landing/Dockerfile has only one output stage (runner) as default last stage"

requirements-completed:
  - INFRA-04
  - INFRA-05

# Metrics
duration: 2min
completed: 2026-06-01
---

# Phase 8 Plan 02: Compose Orchestration (Healthcheck + Landing Service) Summary

**Four-service Docker Compose orchestration with postgres pg_isready healthcheck, fastapi health-gated startup, landing service wired to ./landing/Dockerfile, and caddy depending on all three app services**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-01T12:25:47Z
- **Completed:** 2026-06-01T12:27:07Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added `healthcheck` block to `postgres` service: `pg_isready -U ppuser -d performance_plus` with interval 10s, timeout 5s, retries 5, start_period 30s — prevents FastAPI `init_db()` connection race on cold start
- Converted `fastapi.depends_on` from list form (`- postgres`) to dict form with `condition: service_healthy` — FastAPI now waits until postgres passes pg_isready before starting
- Added `landing` service block: `build.context: ./landing`, `restart: unless-stopped`, `networks: [internal]` — no `ports:` (D-03), no `env_file:` (D-14/T-08-07)
- Extended `caddy.depends_on` from `[app]` to `[app, fastapi, landing]` — simple list form per D-10 (no healthcheck condition on caddy)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add postgres healthcheck and update fastapi depends_on** — `1342fbb` (feat)
2. **Task 2: Add landing service and update caddy depends_on** — `e25b8e4` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `compose.yaml` — 4 changes applied:
  1. `postgres` service: `healthcheck` block added after `networks:` key
  2. `fastapi` service: `depends_on` converted from list to dict form with `condition: service_healthy`
  3. `landing` service: new block added between `caddy` and `fastapi` services
  4. `caddy` service: `depends_on` extended from `[app]` to `[app, fastapi, landing]`

## Healthcheck Timing Values

Per RESEARCH.md A1 (Claude's Discretion area — conventional community values):

| Key | Value | Rationale |
|-----|-------|-----------|
| interval | 10s | Check every 10 seconds during startup |
| timeout | 5s | Fail if pg_isready takes > 5s to respond |
| retries | 5 | Mark unhealthy after 5 consecutive failures |
| start_period | 30s | Grace period for postgres cold-start; failures during window don't count toward retries |

## Decisions Made

1. **Healthcheck timing values (10s/5s/5/30s):** Conventional community values per RESEARCH.md A1. These are well-established defaults for postgres in Docker Compose — not benchmarked against actual startup timing, but conservative enough to handle cold-start on typical VPS hardware.

2. **landing service placement:** Inserted between `caddy` and `fastapi` blocks to maintain logical grouping (edge proxy → frontend services → backend service → database).

3. **No structural changes to app, fastapi build, postgres image/env/volumes, networks, or volumes blocks:** Only the specific keys described in the plan were modified; all other keys preserved byte-for-byte.

## Deviations from Plan

None — plan executed exactly as written. All 4 compose.yaml changes applied in 2 tasks, verified, and committed.

## Verification Results

Task 1 acceptance criteria — all passed:
- YAML validity: `yaml.safe_load(open('compose.yaml'))` exits 0
- `services.postgres.healthcheck.test` = `["CMD-SHELL", "pg_isready -U ppuser -d performance_plus"]`
- `services.postgres.healthcheck.interval` = `10s`
- `services.postgres.healthcheck.timeout` = `5s`
- `services.postgres.healthcheck.retries` = `5`
- `services.postgres.healthcheck.start_period` = `30s`
- `services.fastapi.depends_on` is dict (not list)
- `services.fastapi.depends_on.postgres.condition` = `service_healthy`
- `services.postgres.environment.POSTGRES_USER` unchanged (`ppuser`)
- `services.postgres.environment.POSTGRES_DB` unchanged (`performance_plus`)
- `services.app` block unchanged (no `ports` key)

Task 2 acceptance criteria — all passed:
- `services.landing.build.context` = `./landing`
- `services.landing.build` has no `target` key
- `services.landing` has no `ports` key (D-03, T-08-06)
- `services.landing` has no `env_file` key (D-14, T-08-07)
- `services.landing.restart` = `unless-stopped`
- `services.landing.networks` = `["internal"]`
- `services.caddy.depends_on` is a list (not dict) per D-10
- `services.caddy.depends_on` contains exactly `{app, fastapi, landing}`
- `networks.internal.driver` = `bridge` (unchanged)
- `volumes` still contains `caddy_data`, `caddy_config`, `postgres_data`

Test suite: **8 passed** in `tests/test_deploy_config.py` (including `test_compose_app_has_no_published_port` and `test_compose_uses_named_caddy_volumes`).

Full pytest suite: **81 passed, 5 skipped** — identical to Phase 7/Plan 01 baseline. No regressions.

Note: `docker compose config` validation deferred to VPS deploy-time — Docker not present in local dev shell per RESEARCH.md Environment Availability table. The YAML is syntactically valid per `yaml.safe_load` and structurally correct per all acceptance criteria checks.

## Threat Surface Scan

All four STRIDE threats from the plan's threat model were mitigated by mechanical acceptance criteria checks:

| Threat | Control | Status |
|--------|---------|--------|
| T-08-06: landing service host port exposure | `ports:` key absent from landing service (verified via YAML parser) | Mitigated |
| T-08-07: landing env_file leaking secrets | `env_file:` key absent from landing service (verified via YAML parser) | Mitigated |
| T-08-08: fastapi startup race against postgres | `condition: service_healthy` in dict-form depends_on (verified via YAML parser) | Mitigated |
| T-08-09: pg_isready user/db mismatch | healthcheck test = `pg_isready -U ppuser -d performance_plus` matches POSTGRES_USER/POSTGRES_DB (verified via YAML parser) | Mitigated |

No new threat surface introduced beyond what the plan's threat model covered.

## Known Stubs

None — compose.yaml is a pure configuration file; no application code stubs introduced.

## Self-Check: PASSED

- `compose.yaml` exists: FOUND
- Task 1 commit `1342fbb`: FOUND
- Task 2 commit `e25b8e4`: FOUND
- `tests/test_deploy_config.py`: 8 passed
- Full pytest: 81 passed, 5 skipped

---
*Phase: 08-infrastructure-update*
*Completed: 2026-06-01*
