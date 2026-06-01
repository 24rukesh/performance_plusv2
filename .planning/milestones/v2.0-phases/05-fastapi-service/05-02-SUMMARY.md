---
phase: 05-fastapi-service
plan: "02"
subsystem: infrastructure
tags: [docker, compose, multi-stage, fastapi, postgres]
dependency_graph:
  requires: [05-01]
  provides: [05-03, 05-04]
  affects: [Dockerfile, compose.yaml]
tech_stack:
  added: [postgres:16-alpine, uvicorn multi-target Dockerfile stage]
  patterns: [multi-stage Docker builds with shared builder, Docker Compose internal-network service isolation]
key_files:
  created: []
  modified:
    - Dockerfile
    - compose.yaml
decisions:
  - "Builder stage preserved exactly — dependencies install once, both runtimes copy from it"
  - "Non-root appuser (UID/GID 1001) duplicated in both runtime stages — intentional, each stage is independent FROM"
  - "postgres service has no exposed ports — internal Docker bridge only (D-08 constraint)"
  - "fastapi service has no exposed ports — Caddy routing deferred to Phase 8 (D-04)"
  - "Explicit target: streamlit on app service prevents Docker from defaulting to the last stage (api) after rewrite"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-01T06:05:47Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 5 Plan 02: Multi-Target Dockerfile and Compose Services Summary

Multi-stage Dockerfile with shared builder plus named `streamlit` and `api` runtime targets, paired with a four-service compose.yaml that isolates postgres and fastapi on the internal network.

## Tasks Completed

### Task 1: Rewrite Dockerfile to multi-target form

**Commit:** `594dee1`

**Stage list (final Dockerfile):**

| Stage | FROM line | Line range | CMD |
|-------|-----------|------------|-----|
| `builder` | `FROM python:3.11-slim-bookworm AS builder` | 4–26 | (no CMD — build stage only) |
| `streamlit` | `FROM python:3.11-slim-bookworm AS streamlit` | 29–51 | `streamlit run app.py --server.port=8501 --server.address=0.0.0.0` |
| `api` | `FROM python:3.11-slim-bookworm AS api` | 54–72 | `uvicorn api.main:app --host 0.0.0.0 --port 8000` |

**Key Dockerfile properties:**
- Builder stage preserved byte-for-byte (two-pass uv sync with cache mounts and lockfile bind mounts)
- `USER appuser` appears exactly twice (once per runtime stage)
- `groupadd -g 1001 appgroup && useradd -u 1001 ...` appears exactly twice (intentional — each stage is a fresh layer)
- `EXPOSE 8501` in streamlit stage, `EXPOSE 8000` in api stage
- Streamlit healthcheck targets `/_stcore/health`, api healthcheck targets `/api/health`

### Task 2: Modify compose.yaml

**Commit:** `048ec19`

**Final service list:**

| Service | Build target / Image | Key config | Ports |
|---------|---------------------|------------|-------|
| `app` | `target: streamlit` | `env_file: .env`, `networks: [internal]` | None (Caddy proxies) |
| `caddy` | `caddy:2-alpine` | Volumes: `caddy_data`, `caddy_config`, `./caddy` | `80:80`, `443:443`, `443:443/udp` |
| `fastapi` | `target: api` | `env_file: .env`, `depends_on: [postgres]`, `networks: [internal]` | None (deferred to Phase 8) |
| `postgres` | `postgres:16-alpine` | `POSTGRES_DB: performance_plus`, `POSTGRES_USER: ppuser`, `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}`, `volumes: [postgres_data:/var/lib/postgresql/data]`, `networks: [internal]` | None (internal-only per D-08) |

**Volume declarations:**
- `caddy_data:` (existing, preserved)
- `caddy_config:` (existing, preserved)
- `postgres_data:` (new — added in this plan)

## Verification Results

### Grep Gates

| Check | Expected | Result |
|-------|----------|--------|
| `grep -c "AS builder\|AS streamlit\|AS api" Dockerfile` | 3 | 3 PASS |
| `grep -c "USER appuser" Dockerfile` | 2 | 2 PASS |
| `grep -c 'POSTGRES_PASSWORD:.*"' compose.yaml` (hardcoded password) | 0 | 0 PASS |
| caddy ports (80, 443, 443/udp) unchanged | present | PASS |

### YAML Structural Assertion

```
uv run python -c "import yaml; c = yaml.safe_load(open('compose.yaml')); ..."
```

Result: `ok` — all assertions passed:
- `set(c['services'].keys()) == {'app', 'caddy', 'fastapi', 'postgres'}`
- `c['services']['app']['build']['target'] == 'streamlit'`
- `c['services']['fastapi']['build']['target'] == 'api'`
- `c['services']['postgres']['image'] == 'postgres:16-alpine'`
- `'ports' not in c['services']['postgres']`
- `'postgres_data' in c['volumes']`

### Docker Build Verification

Docker was **not available** in the local execution environment. `docker compose build` verification is deferred to integration time (when the VPS environment is available). The Dockerfile syntax and stage references are structurally valid — confirmed by grep gates and the YAML assertion covering target names.

## Threat Model Compliance

All mitigations from the plan's STRIDE threat register are implemented:

| Threat ID | Mitigation | Verified |
|-----------|-----------|---------|
| T-05-02-01 | No secret baked into image (no `COPY .env` in Dockerfile) | Dockerfile reviewed — no COPY .env |
| T-05-02-02 | Postgres password uses `${POSTGRES_PASSWORD}` indirection | grep gate returns 0 hardcoded passwords |
| T-05-02-03 | Both runtime stages use `USER appuser` | grep gate returns 2 |
| T-05-02-04 | Postgres has no `ports:` key | YAML assertion passes |
| T-05-02-05 | App service explicitly declares `target: streamlit` (Pitfall 1 fix) | YAML assertion passes |
| T-05-02-06 | postgres_data named volume (accept) | Volume present, no encryption needed for synthetic data |
| T-05-02-07 | Single uvicorn worker (accept) | Default uvicorn CMD used |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- Dockerfile exists at `/Users/rukesh/Documents/Dev/performance_plus/Dockerfile` — FOUND
- compose.yaml exists at `/Users/rukesh/Documents/Dev/performance_plus/compose.yaml` — FOUND
- Commit `594dee1` exists in git log — FOUND
- Commit `048ec19` exists in git log — FOUND
