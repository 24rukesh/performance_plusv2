---
phase: 08-infrastructure-update
plan: 01
subsystem: infra
tags: [docker, nextjs, alpine, standalone, nodejs]

# Dependency graph
requires:
  - phase: 07-landing-page-ui-polish
    provides: "landing/ Next.js 16 app with NEXT_PUBLIC_API_BASE_URL='' pattern and verified production build"
provides:
  - "landing/next.config.ts with output: standalone directive"
  - "landing/.dockerignore excluding .env* glob (blocks .env.local bake-in)"
  - "landing/Dockerfile — node:20-alpine multi-stage builder+runner, appuser UID 1001"
affects:
  - "08-02 (compose.yaml must reference build: context: ./landing)"
  - "08-03 (Caddyfile catch-all must proxy to landing:3000)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "node:20-alpine multi-stage Dockerfile with Next.js standalone output"
    - "Alpine addgroup/adduser syntax (BusyBox) vs Debian groupadd/useradd"
    - "COPY order: public → mkdir .next → standalone → static (static overlays last)"
    - ".dockerignore .env* glob pattern to block NEXT_PUBLIC_ build-time bake"

key-files:
  created:
    - "landing/.dockerignore"
    - "landing/Dockerfile"
  modified:
    - "landing/next.config.ts"

key-decisions:
  - "npm ci (no --omit=dev): TypeScript compiler and Tailwind PostCSS are devDependencies needed at build time; standalone copy ensures devDeps never reach the runtime image"
  - "HEALTHCHECK omitted from landing/Dockerfile: caddy depends_on for landing has no condition: service_healthy so HEALTHCHECK adds complexity for no functional benefit in Phase 8"
  - ".env* glob (not bare .env): .env.local contains NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 which Next.js reads at build time; bare .env would not exclude .env.local"
  - "Comment adjusted: removed 'useradd' mention from comment text so acceptance criterion grep check passes cleanly"

patterns-established:
  - "Pattern: node:20-alpine Dockerfile uses addgroup/adduser (not groupadd/useradd); GID/UID 1001 consistent with root Dockerfile Python stages"
  - "Pattern: standalone COPY sequence is immutable — reversing static/standalone order silently overwrites traced static assets"

requirements-completed:
  - INFRA-04

# Metrics
duration: 2min
completed: 2026-06-01
---

# Phase 8 Plan 01: Landing Dockerfile + Standalone Config Summary

**Node 20-alpine multi-stage Dockerfile for Next.js 16 standalone server with non-root appuser and .env* exclusion blocking localhost URL bake-in**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-01T12:21:25Z
- **Completed:** 2026-06-01T12:23:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `output: "standalone"` to `landing/next.config.ts` — triggers Next.js to emit `.next/standalone/server.js` during `next build`
- Created `landing/.dockerignore` with `.env*` glob (critical: blocks `.env.local` from baking `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` into the production JS bundle)
- Created `landing/Dockerfile` as Node 20-alpine multi-stage build (builder + runner) using Alpine `addgroup`/`adduser` syntax with appuser UID 1001, correct COPY order, and `CMD ["node", "server.js"]`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add output: standalone to landing/next.config.ts** - `651e02a` (feat)
2. **Task 2: Create landing/.dockerignore** - `14e4f0e` (chore)
3. **Task 3: Create landing/Dockerfile (node:20-alpine multi-stage)** - `55cc8de` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `landing/next.config.ts` — Added `output: "standalone"` to nextConfig; triggers standalone build output consumed by Dockerfile runner stage
- `landing/.dockerignore` — Excludes `node_modules`, `.next`, `.env*` glob, `npm-debug.log*`, `.DS_Store`; negation `!.env.example` preserves template; blocks `.env.local` from build context
- `landing/Dockerfile` — Node 20-alpine multi-stage: builder (npm ci + next build), runner (standalone copy with non-root appuser UID 1001, EXPOSE 3000, CMD ["node", "server.js"])

## Decisions Made

1. **npm ci without --omit=dev in builder stage:** TypeScript compiler and Tailwind PostCSS are `devDependencies` required at build time. The standalone copy to the runtime stage ensures no `node_modules` reach the final image regardless. Using `--omit=dev` would break `next build` for this project.

2. **HEALTHCHECK omitted from landing/Dockerfile:** D-10 specifies caddy's `depends_on` list for the landing service has no `condition: service_healthy`. Adding a Dockerfile HEALTHCHECK would provide observability but adds complexity with no functional benefit in Phase 8 scope.

3. **Comment text adjusted to remove "useradd" string:** The initial comment read "NOT useradd/groupadd — those are Debian-only" which caused the acceptance criterion check `! grep -q 'useradd' landing/Dockerfile` to fail. Comment rewritten to "Alpine BusyBox addgroup/adduser syntax" — same intent, passes grep check. This is a minor deviation: Rule 1 (auto-fix) applied to the comment wording.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comment contained "useradd" string causing acceptance criterion check failure**
- **Found during:** Task 3 verification (post-write acceptance checks)
- **Issue:** Comment `# Non-root user — Alpine BusyBox syntax (NOT useradd/groupadd — those are Debian-only)` triggered `! grep -q 'useradd' landing/Dockerfile` to return FAIL
- **Fix:** Rewrote comment to `# Non-root user — Alpine BusyBox addgroup/adduser syntax (D-05)` — identical intent, no "useradd" string in file
- **Files modified:** `landing/Dockerfile`
- **Verification:** Re-ran all 15 acceptance criteria checks — all PASS
- **Committed in:** 55cc8de (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - comment text causing false grep match)
**Impact on plan:** Trivial. Comment reword only, no functional or security impact.

## Issues Encountered

None beyond the comment grep issue documented above.

## Verification Results

All static checks passed:

```
grep -E 'output:\s*"standalone"' landing/next.config.ts  →  output: "standalone",
grep -c '^\.env\*$' landing/.dockerignore                →  1
FROM node:20-alpine AS runner present                     →  PASS
no useradd in Dockerfile                                  →  PASS
no NEXT_PUBLIC in Dockerfile                              →  PASS
```

Full pytest suite: **81 passed, 5 skipped** — identical to Phase 7 baseline. No regressions.

Docker build verification deferred to VPS deploy-time (Docker not present in local dev shell per RESEARCH.md Environment Availability table). When run on a Docker-equipped host: `docker build --target runner ./landing` must exit 0.

## Threat Surface Scan

All three threat mitigations confirmed implemented:

| Threat | Control | Status |
|--------|---------|--------|
| T-08-01: .env.local baking NEXT_PUBLIC_ into JS bundle | `.env*` glob in `landing/.dockerignore` | Mitigated |
| T-08-02: Container running as root | `USER appuser` (UID 1001) in runner stage | Mitigated |
| T-08-03: NEXT_PUBLIC_* or OPENAI_API_KEY in image layers | No `ENV NEXT_PUBLIC_*`, no `ARG` vars in Dockerfile | Mitigated |
| T-08-04: COPY order tampering | Static COPY line > standalone COPY line (verified by awk) | Mitigated |

No new threat surface introduced beyond what the plan's threat model covered.

## User Setup Required

None — no external service configuration required. Docker build happens at VPS deploy time.

## Next Phase Readiness

- Plan 02 (compose.yaml update) can now reference `build: { context: ./landing }` — `landing/Dockerfile` exists at that location
- Plan 03 (Caddyfile multi-route) catch-all `handle { reverse_proxy landing:3000 }` will route to the landing service started by compose.yaml
- All three required files for the landing container are in place

---
*Phase: 08-infrastructure-update*
*Completed: 2026-06-01*
