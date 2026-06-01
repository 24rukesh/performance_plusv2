# Phase 7: Landing Page & UI Polish - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a Next.js marketing site in a `landing/` subdirectory (TypeScript, App Router, Tailwind CSS) with five sections: hero (with inline waitlist form), How It Works, animated demo preview, Features, and a footer. Separately, polish the existing Streamlit app with a branded header and improved expandable results layout.

Phase 7 scope:
- `landing/` — new Next.js app (hero, How It Works, animated demo, features, waitlist form)
- `app.py` + `ui_helpers.py` — Streamlit branded header (UI-03), expandable results layout (UI-04), link to marketing site (UI-05)
- No Caddy/Docker changes (Phase 8 wires routing and adds the Next.js container)

</domain>

<decisions>
## Implementation Decisions

### Next.js Setup
- **D-01:** Language: **TypeScript**. Use `create-next-app` with `--typescript` flag.
- **D-02:** Router: **App Router** (Next.js 14/15 default).
- **D-03:** Styling: **Tailwind CSS**. Configured via `create-next-app` — fastest path for a single-page marketing site.
- **D-04:** Location: `landing/` subdirectory at the project root. Keeps Next.js isolated from the Python codebase; aligns with the Phase 8 Docker service name.

### Page Sections (LAND-01 through LAND-04)
- **D-05:** **Hero section** — Product name ("Performance Plus"), one-liner value prop, two CTAs: "Try Demo" (links to Streamlit app) and "Join Waitlist" (anchor to waitlist form in same section). Waitlist form is inline in the hero — email input + button, no scroll required.
- **D-06:** **How It Works section** — 3-step horizontal flow: "1. Upload CSV data → 2. AI Analysis → 3. Budget Decisions". Static text + icons, no animation needed.
- **D-07:** **Animated demo section** (LAND-03) — Pure React component with CSS keyframe animation. 3-4 campaign cards fade/slide in sequentially. Cards use hardcoded data matching the existing mock dataset (same campaign names and badge colors as the Streamlit app). No iframe, no GIF, no live data dependency.
  - Badge colors: `#09ab3b` (INCREASE), `#ff2b2b` (PAUSE/DECREASE), `#faca2b` (REVIEW), `#808495` (HOLD) — per D-03 from Phase 1.
  - Campaign names: use names from `data/web_analytics.csv` or the existing fixture (e.g., Google Search, Meta Retargeting).
- **D-08:** **Features section** (LAND-04) — 4 feature cards: Semantic Attribution, CRM Webhook Sync, n8n Automation, Budget Routing. Static content.

### Waitlist Form UX
- **D-09:** Form placement: **inline in the hero section** (email input + submit button). One CTA area, no scroll.
- **D-10:** On success: **replace the input with the confirmation message inline** — "You're on the waitlist! We'll be in touch." (exact string from the API response). No page reload, no modal.
- **D-11:** On 409 (duplicate): show "You're already on the waitlist." inline below the input.
- **D-12:** On 500 / network error: show a generic **"Something went wrong — please try again."** message inline below the input. Do NOT expose raw API error detail to visitors.
- **D-13:** API call: `POST /api/waitlist` with `Content-Type: application/json` body `{"email": "..."}`. No API key required (public endpoint from Phase 6).
- **D-14:** During local Next.js dev (`localhost:3000`), the fetch target is `http://localhost:8000/api/waitlist`. In production, Caddy routes `/api` to FastAPI (Phase 8). Use `NEXT_PUBLIC_API_BASE_URL` env var (default: empty string = relative path, which works behind Caddy proxy in production).

### Streamlit UI Polish
- **D-15:** Branded header (UI-03): `st.markdown` with custom HTML — `⚡ Performance Plus` as the product name, with tagline: `"AI-powered budget decisions from your CRM notes"`. Use existing IBM Plex Sans font already loaded in `app.py`. Place at top of main content area (not sidebar).
- **D-16:** Landing page link (UI-05): Visible link in the branded header area — e.g., `"← Back to site"` or `"Visit performanceplus.ai"`. Render as a small anchor tag in the header HTML. Target URL: hardcode as `"/"` (relative, works behind Caddy routing in Phase 8) or use a `SITE_URL` env var.
- **D-17:** Improved results layout (UI-04): Replace the current results table with **`st.expander` per campaign**. Each expander header shows: campaign name + action badge (colored pill) + % change. Expanding reveals the full AI reasoning text inline. Reuse existing badge color constants from `ui_helpers.py`.

### Claude's Discretion
- Next.js project exact version (use latest stable Next.js 14/15 via `create-next-app`).
- Specific Tailwind class choices, spacing, and responsive breakpoints.
- Whether to include a `next.config.js` rewrite rule for `/api` → `NEXT_PUBLIC_API_BASE_URL` in local dev.
- Footer content (simple copyright line is fine).
- Whether to extract the demo animation into a separate component file.
- Exact wording of feature card descriptions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `./CLAUDE.md` — Stack constraints (Python 3.11, Streamlit, uv). Read "TL;DR" and "What NOT to Use".
- `.planning/PROJECT.md` — v2.0 goals, constraints, core value prop.
- `.planning/ROADMAP.md` — Phase 7 success criteria (5 items that must be TRUE), requirements LAND-01–04, UI-03–05.
- `.planning/REQUIREMENTS.md` §Landing Page and §Streamlit UI Polish — full requirement text.

### Existing Code to Extend (Streamlit polish)
- `./app.py` — Current Streamlit app (141 lines). Branded header goes at top of main area. Results rendering uses `ui_helpers.build_results_table_html()` — replace/supplement with `st.expander` pattern.
- `./ui_helpers.py` — Badge color constants and HTML helpers. Reuse badge colors for demo animation AND Streamlit expander headers.

### Prior Phase Patterns
- `.planning/phases/06-waitlist-backend/06-CONTEXT.md` — D-11 (CORSMiddleware wildcard CORS already active), D-12 (POST /api/waitlist is public, no API key), D-10 (success message exact string).
- `.planning/phases/01-design-user-flow-artifacts/` — Badge color decisions (D-03: #09ab3b/#ff2b2b/#faca2b/#808495) and screen label conventions.

</canonical_refs>

<specifics>
## Specific Ideas

- Demo animation: cards should animate with a short stagger delay (e.g., 0.2s apart) so they appear to "load in" sequentially — matches the feeling of an AI generating results one by one.
- Waitlist form: the submit button should show a loading state while the fetch is in-flight (e.g., "Joining..." or a spinner) before the success/error message appears.
- The "Try Demo" CTA should open the Streamlit app in a new tab (or link to `/app` which Caddy will route in Phase 8).

</specifics>

<deferred>
## Deferred Ideas

- Dark mode toggle — out of scope for Phase 7; not in requirements.
- SEO meta tags / Open Graph — nice to have but not a Phase 7 success criterion.
- Testimonials section — no testimonials yet; belongs in a future phase.
- Pricing section — waitlist-only for v2.0; pricing is post-launch scope.
- Next.js analytics (Vercel Analytics, PostHog) — deferred; Phase 8 focuses on infra, analytics is v3+.

</deferred>

---

*Phase: 07-landing-page-ui-polish*
*Context gathered: 2026-06-01 via discuss-phase*
