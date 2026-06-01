---
phase: 07-landing-page-ui-polish
plan: 02
subsystem: ui
tags: [nextjs, tailwindcss, typescript, next-font, ibm-plex, badge-tokens, env]

# Dependency graph
requires:
  - phase: 07-01
    provides: landing/ scaffold committed as part of Streamlit polish plan
provides:
  - "Tailwind v4 @theme block with 10 brand/badge hex tokens in landing/app/globals.css"
  - "IBM Plex Sans (400, 600) + IBM Plex Mono (400) self-hosted via next/font/google with CSS variables"
  - "landing/components/badge-tokens.ts mirroring ui_helpers.py badge color/label mappings"
  - "landing/.env.example documenting NEXT_PUBLIC_API_BASE_URL with production guidance"
  - "fadeSlideIn @keyframes for DemoAnimation.tsx (Plan 04)"
affects:
  - 07-03-landing-hero-howit-works
  - 07-04-landing-demo-features-footer

# Tech tracking
tech-stack:
  added:
    - "next@16.2.6 (already scaffolded in 07-01)"
    - "@heroicons/react@2.2.0 (already installed in 07-01)"
    - "tailwindcss@4.x with @tailwindcss/postcss (Tailwind v4 CSS-first config)"
    - "IBM_Plex_Sans and IBM_Plex_Mono from next/font/google"
  patterns:
    - "Tailwind v4 @theme block in globals.css for custom color tokens (no tailwind.config.ts)"
    - "next/font/google CSS variable pattern: variable: '--font-sans' applied to <html> element"
    - "badge-tokens.ts as shared cross-stack constant file mirroring Python ui_helpers.py"
    - "NEXT_PUBLIC_* env vars in landing/.env.local (local dev only, unset in production)"

key-files:
  created:
    - "landing/components/badge-tokens.ts"
    - "landing/.env.example"
    - "landing/.env.local (gitignored)"
  modified:
    - "landing/app/globals.css"
    - "landing/app/layout.tsx"
    - "landing/app/page.tsx"
    - "landing/.gitignore (added !.env.example exception)"

key-decisions:
  - "Tailwind v4 @theme block (not tailwind.config.ts) is the single source of truth for brand/badge color tokens"
  - "IBM Plex fonts loaded via next/font/google (self-hosted at build time, zero layout shift)"
  - "badge-tokens.ts is LOCKED — any hex change must be matched in ui_helpers.py to maintain cross-stack visual parity"
  - "NEXT_PUBLIC_API_BASE_URL left UNSET in production builds; Caddy routes /api from same origin (Phase 8)"
  - "landing/.gitignore updated to allow .env.example to be committed (added !.env.example)"

patterns-established:
  - "Pattern S-1: Color Token Mirror — globals.css @theme hex values must equal ui_helpers.py values"
  - "Pattern: CSS variable font loading with ibmPlexSans.variable + ibmPlexMono.variable on <html>"

requirements-completed:
  - LAND-01
  - LAND-03

# Metrics
duration: 22min
completed: 2026-06-01
---

# Phase 7 Plan 02: Landing Scaffold + Design System Foundation Summary

**Next.js 16 landing/ app scaffolded with Tailwind v4 @theme brand/badge tokens, IBM Plex fonts via next/font/google, badge-tokens.ts mirroring ui_helpers.py palette, and .env.example env contract**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-06-01T10:52:51Z
- **Completed:** 2026-06-01T11:15:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Tailwind v4 @theme block in globals.css defining all 10 brand and badge hex tokens — generates bg-brand-*, text-brand-*, border-brand-* Tailwind utility classes automatically
- IBM Plex Sans (400, 600) + IBM Plex Mono (400) self-hosted via next/font/google as --font-sans/--font-mono CSS variables; applied to root <html> element
- badge-tokens.ts with BADGE_COLORS and PCT_COLOR constants, locked hex values matching ui_helpers.py exactly for cross-stack visual parity
- .env.example documents NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 with production guidance (leave UNSET)
- fadeSlideIn @keyframes defined in globals.css for DemoAnimation.tsx (Plan 04)
- tsc --noEmit exits 0 with all files

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold landing/ with create-next-app + install Heroicons** - `55bd5d0` (feat — committed by 07-01 agent as part of Streamlit polish plan)
2. **Task 2: Wire Tailwind v4 @theme tokens + IBM Plex fonts + badge-tokens.ts + env files** - `9699e78` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `landing/app/globals.css` - @import "tailwindcss", @theme block with 10 brand/badge tokens, fadeSlideIn keyframes
- `landing/app/layout.tsx` - IBM Plex Sans/Mono next/font/google loading, Metadata title, bg-brand-bg body, Server Component
- `landing/app/page.tsx` - Empty placeholder Server Component (`<main className="min-h-screen" />`)
- `landing/components/badge-tokens.ts` - BADGE_COLORS (increase/pause/decrease/insufficient_data) + PCT_COLOR, as const, locked hex values
- `landing/.env.example` - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 with production comment
- `landing/.env.local` - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 (gitignored)
- `landing/.gitignore` - Added `!.env.example` exception to allow template file to be committed

## Decisions Made
- Tailwind v4 uses @theme in globals.css (not tailwind.config.ts) — this is the CSS-first config approach and avoids the Tailwind v4 "silently ignores config" pitfall
- IBM_Plex_Sans and IBM_Plex_Mono imported from next/font/google; both are confirmed exports in next/dist/compiled/@next/font/dist/google/index.d.ts
- badge-tokens.ts uses `as const` for literal-type inference; file is the single TypeScript source of truth for badge colors consumed by DemoAnimation.tsx and other components in Plans 03/04
- NEXT_PUBLIC_API_BASE_URL production strategy: leave UNSET in Docker build, use relative /api/waitlist path, Caddy routes to FastAPI in Phase 8

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added !.env.example exception to landing/.gitignore**
- **Found during:** Task 2 (creating env files)
- **Issue:** The scaffold's landing/.gitignore used `.env*` which blocked git from staging landing/.env.example. The plan requires this file to be committed (it's a template, not a secret).
- **Fix:** Added `!.env.example` negation line to landing/.gitignore so the template can be tracked in git while `.env.local` remains gitignored.
- **Files modified:** landing/.gitignore
- **Verification:** `git add landing/.env.example` succeeded after fix
- **Committed in:** 9699e78 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Fix necessary for correctness — .env.example must be committed to serve as documentation for developers. No scope creep.

## Issues Encountered
- Task 1 scaffold was already committed by the 07-01 agent (commit 55bd5d0) which bundled the Next.js scaffold with the Streamlit branded header changes. The scaffold files (package.json, postcss.config.mjs, tsconfig.json, etc.) met all Task 1 acceptance criteria. Task 2 proceeded immediately without re-running create-next-app.

## User Setup Required
None — no external service configuration required. `landing/.env.local` is created with the local dev default value.

## Next Phase Readiness
- Tailwind v4 @theme tokens available: `bg-brand-bg`, `text-brand-text`, `bg-brand-accent`, `bg-badge-increase`, `bg-badge-pause`, `bg-badge-decrease`, `bg-badge-hold`, `border-brand-border`, etc.
- Font CSS variables available: `var(--font-sans)` (IBM Plex Sans) and `var(--font-mono)` (IBM Plex Mono)
- `badge-tokens.ts` exports BADGE_COLORS and PCT_COLOR for DemoAnimation.tsx and any badge-rendering component
- Plan 03 (Hero + HowItWorks sections) can import from globals.css utility classes directly
- Plan 04 (Demo + Features + Footer) can import BADGE_COLORS from landing/components/badge-tokens.ts

---
*Phase: 07-landing-page-ui-polish*
*Completed: 2026-06-01*
