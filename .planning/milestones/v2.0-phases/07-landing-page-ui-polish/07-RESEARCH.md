# Phase 7: Landing Page & UI Polish - Research

**Researched:** 2026-06-01
**Domain:** Next.js 16 marketing site + Streamlit UI polish + cross-stack API integration
**Confidence:** HIGH (verified versions, official docs, existing codebase confirmed)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Next.js Setup**
- **D-01:** Language: **TypeScript**. Use `create-next-app` with `--typescript` flag.
- **D-02:** Router: **App Router** (Next.js 14/15 default — note: Next.js 16 is current; App Router remains default).
- **D-03:** Styling: **Tailwind CSS**. Configured via `create-next-app` — fastest path for a single-page marketing site.
- **D-04:** Location: `landing/` subdirectory at the project root. Keeps Next.js isolated from the Python codebase; aligns with the Phase 8 Docker service name.

**Page Sections (LAND-01 through LAND-04)**
- **D-05:** **Hero section** — Product name ("Performance Plus"), one-liner value prop, two CTAs: "Try Demo" (links to Streamlit app) and "Join Waitlist" (anchor to waitlist form in same section). Waitlist form is inline in the hero — email input + button, no scroll required.
- **D-06:** **How It Works section** — 3-step horizontal flow: "1. Upload CSV data → 2. AI Analysis → 3. Budget Decisions". Static text + icons, no animation needed.
- **D-07:** **Animated demo section** (LAND-03) — Pure React component with CSS keyframe animation. 3-4 campaign cards fade/slide in sequentially. Cards use hardcoded data matching the existing mock dataset (same campaign names and badge colors as the Streamlit app). No iframe, no GIF, no live data dependency.
  - Badge colors: `#09ab3b` (INCREASE), `#ff2b2b` (PAUSE/DECREASE), `#faca2b` (REVIEW), `#808495` (HOLD) — per D-03 from Phase 1.
  - Campaign names: use names from `data/web_analytics.csv` or the existing fixture (e.g., Google Search, Meta Retargeting).
- **D-08:** **Features section** (LAND-04) — 4 feature cards: Semantic Attribution, CRM Webhook Sync, n8n Automation, Budget Routing. Static content.

**Waitlist Form UX**
- **D-09:** Form placement: **inline in the hero section** (email input + submit button). One CTA area, no scroll.
- **D-10:** On success: **replace the input with the confirmation message inline** — "You're on the waitlist! We'll be in touch." (exact string from the API response). No page reload, no modal.
- **D-11:** On 409 (duplicate): show "You're already on the waitlist." inline below the input.
- **D-12:** On 500 / network error: show a generic **"Something went wrong — please try again."** message inline below the input. Do NOT expose raw API error detail to visitors.
- **D-13:** API call: `POST /api/waitlist` with `Content-Type: application/json` body `{"email": "..."}`. No API key required (public endpoint from Phase 6).
- **D-14:** During local Next.js dev (`localhost:3000`), the fetch target is `http://localhost:8000/api/waitlist`. In production, Caddy routes `/api` to FastAPI (Phase 8). Use `NEXT_PUBLIC_API_BASE_URL` env var (default: empty string = relative path, which works behind Caddy proxy in production).

**Streamlit UI Polish**
- **D-15:** Branded header (UI-03): `st.markdown` with custom HTML — `⚡ Performance Plus` as the product name, with tagline: `"AI-powered budget decisions from your CRM notes"`. Use existing IBM Plex Sans font already loaded in `app.py`. Place at top of main content area (not sidebar).
- **D-16:** Landing page link (UI-05): Visible link in the branded header area — e.g., `"← Back to site"` or `"Visit performanceplus.ai"`. Render as a small anchor tag in the header HTML. Target URL: hardcode as `"/"` (relative, works behind Caddy routing in Phase 8) or use a `SITE_URL` env var.
- **D-17:** Improved results layout (UI-04): Replace the current results table with **`st.expander` per campaign**. Each expander header shows: campaign name + action badge (colored pill) + % change. Expanding reveals the full AI reasoning text inline. Reuse existing badge color constants from `ui_helpers.py`.

### Claude's Discretion

- Next.js project exact version (use latest stable Next.js 14/15 via `create-next-app` — see Standard Stack table; latest stable is 16.2.6 as of June 2026).
- Specific Tailwind class choices, spacing, and responsive breakpoints.
- Whether to include a `next.config.js` rewrite rule for `/api` → `NEXT_PUBLIC_API_BASE_URL` in local dev.
- Footer content (simple copyright line is fine).
- Whether to extract the demo animation into a separate component file.
- Exact wording of feature card descriptions.

### Deferred Ideas (OUT OF SCOPE)

- Dark mode toggle — out of scope for Phase 7; not in requirements.
- SEO meta tags / Open Graph — nice to have but not a Phase 7 success criterion.
- Testimonials section — no testimonials yet; belongs in a future phase.
- Pricing section — waitlist-only for v2.0; pricing is post-launch scope.
- Next.js analytics (Vercel Analytics, PostHog) — deferred; Phase 8 focuses on infra, analytics is v3+.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LAND-01 | Hero section with product name, one-liner value prop, "Try Demo" CTA opening the Streamlit app, and "Join Waitlist" CTA | Standard Stack (Next.js + Tailwind), Architecture Patterns §Hero section composition, UI-SPEC §Section 1 Hero (copy locked), Code Examples §Hero/CTA pair |
| LAND-02 | "How It Works" 3-step section (Upload → AI Analysis → Budget Decisions) | Architecture Patterns §3-column responsive grid (`grid-cols-1 md:grid-cols-3`), UI-SPEC §Section 2 (copy locked) |
| LAND-03 | Inline animated demo preview of campaign cards with action badges, no leaving the page | Code Examples §CSS keyframe + IntersectionObserver pattern, Don't Hand-Roll table (use IntersectionObserver, NOT framer-motion), UI-SPEC §Animated Demo Spec (badge colors locked, timing locked) |
| LAND-04 | Features section: semantic attribution, CRM webhook sync, n8n automation, budget routing | Architecture Patterns §Feature card grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`), UI-SPEC §Section 4 (copy locked) |
| UI-03 | Streamlit branded header with product name, icon, tagline | Architecture Patterns §Streamlit branded header, Code Examples §st.markdown HTML branded header (HTML provided verbatim in UI-SPEC §Streamlit Polish) |
| UI-04 | Campaign results in improved layout (expandable detail rows showing reasoning inline) | Standard Stack §Streamlit st.expander, Common Pitfalls §Pitfall 5 (no HTML in expander label), Code Examples §Streamlit expander loop |
| UI-05 | Visible link in Streamlit header/sidebar to marketing landing page | Code Examples §st.markdown header HTML includes `<a href="/">` (verbatim in UI-SPEC); Don't Hand-Roll (do NOT use st.sidebar — header pattern locked) |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Python 3.11** runtime — already pinned in `pyproject.toml` (`requires-python = ">=3.11"`).
- **Streamlit >=1.40,<2.0** — already in dependencies; `st.expander`, `st.markdown(unsafe_allow_html=True)`, and `st.badge` are all available.
- **`uv` is the canonical Python packager** — do NOT add `pip install` instructions in Phase 7 outputs. Streamlit changes happen in `app.py` directly; no new Python deps required.
- **No new Python dependencies expected** — UI-03/04/05 reuse existing `streamlit`, `ui_helpers.py`, and Pydantic models. Verify before adding any.
- **`.env` is gitignored.** `.env.example` is the source-of-truth template for env var names. Any new env var (e.g., `NEXT_PUBLIC_API_BASE_URL` for local Next.js dev, optional `SITE_URL` for Streamlit) must be added to `.env.example` if it ships in the Python-side compose. Next.js's own `.env.local` is a separate file inside `landing/` and is gitignored by `create-next-app`'s default `.gitignore`.
- **Docker base for Streamlit is `python:3.11-slim-bookworm`** — Phase 7 must not touch `Dockerfile` (Phase 8 owns Next.js container + Caddy rewiring per Phase 8 success criteria).
- **`unsafe_allow_html=True`** is already used liberally in `ui_helpers.py` and `app.py` — content is fully developer-controlled (no user-supplied HTML), so the XSS risk does not apply. Keep this discipline: never interpolate user-supplied strings into `unsafe_allow_html` markup.
- **GSD Workflow Enforcement** — all file edits must go through GSD commands (`/gsd:execute-phase` for Phase 7 plans).

## Summary

Phase 7 has two **distinct, parallelizable** surfaces:

1. **Next.js marketing site (`landing/`)** — a *brand-new* Next.js 16 + TypeScript + Tailwind v4 + App Router project, scaffolded via `npx create-next-app@latest landing --ts --tailwind --eslint --app --src-dir=false --import-alias '@/*' --yes`. Single page (`app/page.tsx`) composed of five sections (Hero, How It Works, Animated Demo, Features, Footer) plus one inline waitlist form with React state. No backend logic in Next.js — it's a static-render single-page site that calls FastAPI's `/api/waitlist` from the client.

2. **Streamlit polish (`app.py`, `ui_helpers.py`)** — three small but surgical changes: (a) replace `st.title()` + `st.write()` at top with an `st.markdown(unsafe_allow_html=True)` branded header (UI-03 + UI-05 combined per UI-SPEC HTML block), and (b) replace `build_results_table_html(result)` invocation with an `st.expander`-per-campaign loop (UI-04). Both reuse existing `_badge_html`/`_pct_html` helpers from `ui_helpers.py`.

**Critical findings shaping the plan:**
- `create-next-app@latest` (16.2.6 as of 2026-05-31) defaults to **Tailwind CSS v4**, which uses CSS-first config via `@theme` directive in `globals.css` — NOT `tailwind.config.ts`. The UI-SPEC's `tailwind.config.ts` snippet for custom colors must be translated into a `globals.css` `@theme` block. [VERIFIED: nextjs.org/docs/app/api-reference/cli/create-next-app, last-updated 2026-05-31] [VERIFIED: tailwindcss.com/docs/upgrade-guide]
- `st.expander` labels do **NOT** support HTML or color directives — only bold, italics, strikethrough, inline code, links, images. UI-SPEC already calls this out and prescribes the workaround (render badge HTML inside expander body, plain-text label outside). [VERIFIED: docs.streamlit.io/develop/api-reference/layout/st.expander]
- `NEXT_PUBLIC_*` env vars are **baked at build time** and immutable in the Docker image. UI-SPEC's "leave unset in production = relative path" approach is correct and sidesteps the issue entirely. [VERIFIED: vercel/next.js GitHub discussion #87229]
- Phase 6 already enabled `CORSMiddleware(allow_origins=["*"])` in `api/main.py` — local Next.js dev at `localhost:3000` can hit `http://localhost:8000/api/waitlist` without CORS gymnastics. [VERIFIED: api/main.py line 33]

**Primary recommendation:** Scaffold the Next.js app with the canonical `create-next-app` flags into `landing/`, write components against Tailwind v4's `@theme` block (NOT a `tailwind.config.ts`), gate the demo animation on `IntersectionObserver` to avoid pre-scroll playback, and keep the Streamlit polish to a 30-line diff in `app.py` plus zero changes to `ui_helpers.py` (it already has every helper needed).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Hero / static content render (LAND-01, 02, 04) | **Next.js Server Component** (`app/page.tsx`) | CDN/static (after Phase 8 standalone build) | Static marketing copy — no client interactivity needed in these sections; Server Components are the default and ship zero JS for the static markup. |
| Animated demo (LAND-03) | **Next.js Client Component** (`components/DemoAnimation.tsx` with `"use client"`) | Browser (CSS engine for keyframes) | Requires `useEffect` + `IntersectionObserver` to gate animation start — client-side only. |
| Waitlist form interaction (D-09 to D-12) | **Next.js Client Component** (`components/HeroSection.tsx` or extracted form) | API/Backend (FastAPI POST `/api/waitlist`) | Needs `useState` for submit/success/error states + `onSubmit` event handler — requires `"use client"`. The actual persistence + email notification logic was already shipped in Phase 6 — Next.js is purely the form UI. |
| Font loading | **Next.js Server / build pipeline** (`next/font/google` in `app/layout.tsx`) | Browser (CSS variables apply at render) | `next/font/google` self-hosts the woff2 files at build time → zero layout shift, no Google CDN at runtime. |
| Streamlit branded header (UI-03, UI-05) | **Streamlit Server** (Python) | Browser (renders HTML via `unsafe_allow_html`) | Plain `st.markdown` HTML block — no interactivity beyond a static anchor link. |
| Streamlit expandable results (UI-04) | **Streamlit Server** (Python) | Browser (Streamlit's built-in expander widget) | `st.expander` is a Streamlit-native widget — state managed server-side in Streamlit's runtime. |
| Cross-origin fetch (local dev only) | **FastAPI** (already has `CORSMiddleware(allow_origins=["*"])`) | — | Phase 6 already shipped CORS. In production, Caddy serves both Next.js and FastAPI from the same origin, so CORS becomes moot. |

## Standard Stack

### Core (Next.js side — `landing/`)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `next` | **16.2.6** (latest stable as of 2026-05-31) | React framework + App Router + Server Components + standalone Docker output | Defaults install TypeScript + Tailwind v4 + ESLint + App Router + Turbopack — exactly Phase 7's requirements. [VERIFIED: npm view next version → 16.2.6] |
| `react` | **19.2.6** (pinned by Next.js 16) | UI runtime | Pinned transitively by Next.js 16; do not pin separately. [VERIFIED: npm view react version → 19.2.6] |
| `react-dom` | **19.2.6** | Browser renderer | Pinned transitively by Next.js 16. |
| `typescript` | **6.0.3** (latest stable) | Static types | Defaulted by `create-next-app`'s `--ts` flag. [VERIFIED: npm view typescript version → 6.0.3] |
| `tailwindcss` | **4.3.0** (latest stable) | Utility CSS | Defaulted by `create-next-app`'s `--tailwind` flag. **v4 uses CSS-first `@theme` config — NOT `tailwind.config.ts`.** [VERIFIED: npm view tailwindcss version → 4.3.0] |
| `@tailwindcss/postcss` | latest | PostCSS plugin for Tailwind v4 | Required by Next.js — the "zero config" story is only fully true for Vite; Next.js needs a thin `postcss.config.mjs`. [CITED: designrevision.com/blog/tailwind-nextjs-setup] |

### Supporting (Next.js side)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@heroicons/react` | **2.2.0** | SVG icons for Features section | Inline SVG alternative is also acceptable per UI-SPEC. If installed, tree-shaking ensures only imported icons ship. License: MIT. [VERIFIED: npm view @heroicons/react version → 2.2.0] |
| `next/font/google` | (built into Next.js) | IBM Plex Sans + IBM Plex Mono with zero layout shift | Required by UI-SPEC §Typography. Self-hosts fonts at build time. |

### Core (Streamlit side — already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `streamlit` | `>=1.40,<2.0` (already in `pyproject.toml`) | Adds `st.expander`, `st.markdown(unsafe_allow_html=True)`, `st.caption`, `st.set_page_config` | All needed widgets are already shipped in the installed version. **No new Python deps for Phase 7.** [VERIFIED: pyproject.toml line 7] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Next.js 16 + Tailwind v4 | Next.js 15 + Tailwind v3 | v3 lets you reuse the UI-SPEC's `tailwind.config.ts` block verbatim, but you must pin `next@15`, `tailwindcss@3`, and pass `--no-` flags. v4 is the current default; the @theme translation is mechanical and small. **Recommend v4** — match defaults. |
| `@heroicons/react` npm pkg | Inline SVG paths from heroicons.com | Inline SVG = zero npm dependency, smaller bundle, but more component code. Both are MIT. UI-SPEC permits either. **Recommend `@heroicons/react`** — tree-shaking handles bundle size; cleaner code. |
| `next/font/google` | `<link>` to fonts.googleapis.com (the existing Streamlit approach) | Google CDN link causes FOUT/layout shift and an external request at every page load. `next/font/google` self-hosts at build → zero shift, zero runtime CDN call. **Always use `next/font/google` on the Next.js side.** |
| `framer-motion` | Pure CSS `@keyframes` + IntersectionObserver | UI-SPEC explicitly forbids framer-motion. Pure CSS is ~300 bytes vs ~50KB framer-motion. **Recommend CSS keyframes** (already in UI-SPEC). |
| `st.sidebar` link to landing page | Inline anchor in branded header | UI-SPEC and D-16 lock the link into the header — visible on every screen without requiring sidebar expansion. **Use header HTML block.** |

**Installation (Next.js side):**

```bash
# In project root
npx create-next-app@latest landing --ts --tailwind --eslint --app --no-src-dir --import-alias '@/*' --yes
cd landing
npm install @heroicons/react
```

**Note on `--yes` flag:** `--yes` accepts the recommended defaults (TypeScript, ESLint, Tailwind, App Router, AGENTS.md). The explicit flags above override prompts deterministically for scripting; either combination works. [VERIFIED: nextjs.org/docs/app/api-reference/cli/create-next-app]

**Version verification command for the planner / executor:**

```bash
npm view next version           # expect 16.x
npm view tailwindcss version    # expect 4.x  ← v4 uses @theme, not tailwind.config.ts
npm view @heroicons/react version
```

**No Streamlit-side installs:** `pyproject.toml` is unchanged. Do NOT run `uv add streamlit` or any sync command in Phase 7 Streamlit polish tasks.

## Architecture Patterns

### System Architecture Diagram

```
                       ┌───────────────────────────────────────────────┐
                       │             Browser (visitor)                  │
                       └────────┬──────────────────────┬───────────────┘
                                │                      │
                  GET /          │      POST /api/      │
                  (static HTML)  │      waitlist        │  GET /app
                                 │      (JSON body)     │  (Streamlit)
                                 ▼                      ▼
            ┌──────────────────────────────┐    ┌──────────────────────────┐
            │  Next.js (`landing/`)        │    │  FastAPI (api/main.py)   │
            │   ──────────────────         │    │   ────────────────────   │
            │  app/layout.tsx              │◄───┤  POST /api/waitlist      │
            │   ├─ next/font/google        │    │   ↳ insert_waitlist_email│
            │   └─ <html><body>            │    │   ↳ send_waitlist_       │
            │  app/page.tsx                │    │     notification         │
            │   ├─ HeroSection             │    │  CORSMiddleware(*)       │
            │   │   └─ WaitlistForm        │    └────────────┬─────────────┘
            │   │      └─ useState         │                 │
            │   │      └─ fetch(POST)──────┼─────────────────┘
            │   ├─ HowItWorksSection       │
            │   ├─ DemoAnimation           │    ┌──────────────────────────┐
            │   │   └─ IntersectionObserver│    │  Streamlit (app.py)      │
            │   │   └─ @keyframes          │    │   ────────────────       │
            │   ├─ FeaturesSection         │    │  st.markdown(            │
            │   │   └─ Heroicons SVG       │    │     branded header HTML, │
            │   └─ Footer                  │    │     unsafe_allow_html)   │
            │  globals.css                 │    │   ├─ ⚡ Performance Plus │
            │   └─ @theme { brand colors } │    │   └─ <a href="/">← Back  │
            └──────────────────────────────┘    │  st.expander per campaign│
                                                │   ├─ badge_html (body)   │
                                                │   ├─ pct_html (body)     │
                                                │   └─ semantic_reasoning  │
                                                └──────────────────────────┘
```

Data flow: A visitor lands on `/` → Next.js serves a fully server-rendered HTML page from `app/page.tsx`. Scroll triggers `IntersectionObserver` in `DemoAnimation.tsx` → switches `animation-play-state: paused → running`. Email submission in `HeroSection.tsx` (client component) → fetch POST `/api/waitlist` → FastAPI returns 200/409/500 → React state renders success/error message inline. Separately: a user clicks "Try Demo" → opens `/app` (Caddy proxies to Streamlit). The Streamlit branded header contains a "← Back to site" anchor that returns the user to `/`.

### Component Responsibilities (Next.js)

| File | Responsibility | Server/Client |
|------|----------------|----------------|
| `landing/app/layout.tsx` | Load IBM Plex Sans/Mono fonts via `next/font/google`, apply CSS variables to `<html>`, set page title from UI-SPEC | Server Component |
| `landing/app/page.tsx` | Compose Hero + HowItWorks + DemoAnimation + Features + Footer (top-down) | Server Component |
| `landing/app/globals.css` | `@import "tailwindcss";` + `@theme { ...brand colors, font vars }` + `@keyframes fadeSlideIn` | CSS (build-time) |
| `landing/components/HeroSection.tsx` | Product name + value prop + two CTAs + inline `WaitlistForm` | **Client** (`"use client"` for form state) |
| `landing/components/HowItWorksSection.tsx` | 3-step horizontal grid with step numbers, titles, descriptions | Server Component |
| `landing/components/DemoAnimation.tsx` | 4 hardcoded campaign cards + CSS keyframe + IntersectionObserver | **Client** (`"use client"` for `useEffect`) |
| `landing/components/FeaturesSection.tsx` | 4-card grid with Heroicons | Server Component |
| `landing/components/Footer.tsx` | Copyright line | Server Component |
| `landing/postcss.config.mjs` | `{ plugins: { "@tailwindcss/postcss": {} } }` | Build config |
| `landing/next.config.ts` | Empty for Phase 7. Phase 8 will add `output: "standalone"` for Dockerization. | Build config |
| `landing/.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` for local dev only — gitignored | Env |
| `landing/.env.example` | Document `NEXT_PUBLIC_API_BASE_URL` (empty in prod) so future contributors know it exists | Env template |

### Component Responsibilities (Streamlit)

| File | Responsibility | Change Type |
|------|----------------|-------------|
| `app.py` lines 60–61 | **Delete** `st.title("Performance Plus")` + `st.write("Autonomous Semantic Attribution Engine")`. Replace with `st.markdown(BRANDED_HEADER_HTML, unsafe_allow_html=True)` using the exact HTML from UI-SPEC §Streamlit Polish §Branded Header HTML. | Edit |
| `app.py` line 140 | **Replace** `st.markdown(build_results_table_html(result), unsafe_allow_html=True)` with a `for campaign in result.campaigns:` loop using `st.expander` (header = plain text `f"{campaign.campaign_id} — {campaign.budget_action.upper()} {pct_display}"`; body uses `st.markdown(...badge_html + pct_html, unsafe_allow_html=True)` + `st.write(campaign.semantic_reasoning)` + `st.caption(...confidence + evidence_count)`). | Edit |
| `ui_helpers.py` | **No changes needed.** `_badge_html` and `_pct_html` are reused as-is. `build_results_table_html` becomes orphaned but does no harm — leave it (it's still referenced by tests? — verify in plan). | Untouched |

### Pattern 1: Tailwind v4 `@theme` token wiring (UI-SPEC color translation)

**What:** Tailwind v4 no longer auto-detects `tailwind.config.ts`. Custom colors and font variables must be declared via the `@theme` directive in `globals.css`. The UI-SPEC's TypeScript color block must be ported to CSS custom properties.

**When to use:** Always, for Phase 7 — this is how Tailwind v4 works.

**Example:**

```css
/* landing/app/globals.css — Source: tailwindcss.com/docs/upgrade-guide */
@import "tailwindcss";

@theme {
  /* Brand palette (from UI-SPEC §Color System) */
  --color-brand-bg:        #0a0a0f;
  --color-brand-surface:   #13131a;
  --color-brand-border:    #1e1e2e;
  --color-brand-muted:     #6b7280;
  --color-brand-text:      #f0f2f6;
  --color-brand-accent:    #f63366;

  /* Badge palette (locked from ui_helpers.py) */
  --color-badge-increase:  #09ab3b;
  --color-badge-pause:     #ff2b2b;
  --color-badge-decrease:  #faca2b;
  --color-badge-hold:      #808495;

  /* Font variables (set by next/font/google in layout.tsx) */
  --font-sans: var(--font-sans);
  --font-mono: var(--font-mono);
}

/* Demo animation keyframe — referenced by DemoAnimation.tsx */
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

Tailwind v4 maps `--color-brand-accent` → utility `bg-brand-accent`, `text-brand-accent`, `border-brand-accent`. The UI-SPEC's Tailwind class names (e.g., `bg-brand-bg`, `text-badge-increase`) work unchanged once these `@theme` tokens are defined.

### Pattern 2: `next/font/google` with Tailwind v4 (zero layout shift)

**What:** Self-host IBM Plex Sans + Mono at build time, expose them as CSS variables, map them into Tailwind's font-sans / font-mono utilities.

**When to use:** Every page that uses brand typography (i.e., every page in this single-page site).

**Example:**

```tsx
// landing/app/layout.tsx
// Source: nextjs.org/docs/app/getting-started/fonts + tailwindcss.com/docs/upgrade-guide
import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-sans",
  display: "swap",
});
const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Performance Plus — AI Budget Decisions from CRM Notes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${ibmPlexSans.variable} ${ibmPlexMono.variable}`}>
      <body className="bg-brand-bg text-brand-text font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
```

### Pattern 3: Client-side waitlist form with React state

**What:** A `"use client"` form component with `useState` for submitting/idle/success/duplicate/error states. Fetch the API, gate UI on the response status.

**When to use:** The waitlist form in `HeroSection.tsx` (or extracted to `components/WaitlistForm.tsx`).

**Example:**

```tsx
"use client";
// Source: UI-SPEC §Waitlist Form Interaction Contract + Phase 6 API contract
import { useState, FormEvent } from "react";

type Status = "idle" | "submitting" | "success" | "duplicate" | "error";

export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("submitting");
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
      const res = await fetch(`${base}/api/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) setStatus("success");
      else if (res.status === 409) setStatus("duplicate");
      else setStatus("error");
    } catch {
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <p className="mt-4 text-sm text-center text-green-400">
        You&apos;re on the waitlist! We&apos;ll be in touch.
      </p>
    );
  }

  return (
    <div id="waitlist" className="max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-row gap-4">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your work email"
          disabled={status === "submitting"}
          className="flex-1 h-12 px-4 bg-brand-surface border border-brand-border rounded-lg text-brand-text placeholder-brand-muted focus:outline-none focus:ring-2 focus:ring-brand-accent"
        />
        <button
          type="submit"
          disabled={status === "submitting"}
          className="h-12 px-6 bg-brand-accent text-white font-semibold rounded-lg min-w-[120px] disabled:opacity-75 disabled:cursor-not-allowed"
        >
          {status === "submitting" ? "Joining..." : "Join Waitlist"}
        </button>
      </form>
      {status === "duplicate" && (
        <p className="mt-4 text-sm text-center text-brand-muted">You&apos;re already on the waitlist.</p>
      )}
      {status === "error" && (
        <p className="mt-4 text-sm text-center text-red-400">Something went wrong — please try again.</p>
      )}
    </div>
  );
}
```

### Pattern 4: IntersectionObserver-gated CSS animation

**What:** Render demo cards with `animation-play-state: paused`. When the demo section scrolls into view, toggle a class that sets `animation-play-state: running`. Each card gets a `style={{ animationDelay: '0.0s' | '0.2s' | '0.4s' | '0.6s' }}` for the stagger.

**When to use:** `DemoAnimation.tsx`. Always — UI-SPEC §Animated Demo Spec explicitly requires this gate.

**Example:**

```tsx
"use client";
// Source: medium.com (Chris Gustin) + UI-SPEC §Animation Timing
import { useEffect, useRef, useState } from "react";

const demoCards = [
  { id: "cmp_b2b_search", label: "B2B Search", action: "increase", pct: "+22%", reasoning: 'High-intent sales notes: "ready to sign", "budget approved"', delay: "0s" },
  { id: "cmp_retargeting", label: "Retargeting", action: "increase", pct: "+15%", reasoning: "Warm leads re-engaging, CRM notes show strong purchase intent", delay: "0.2s" },
  { id: "cmp_competitor_conquest", label: "Competitor Conquest", action: "decrease", pct: "-30%", reasoning: "Low conversion quality, sales notes cite poor fit", delay: "0.4s" },
  { id: "cmp_linkedin_outbound", label: "LinkedIn Outbound", action: "pause", pct: "0%", reasoning: "Insufficient qualified data to justify spend", delay: "0.6s" },
];

export function DemoAnimation() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setAnimate(true); observer.disconnect(); } },
      { threshold: 0.3 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={sectionRef} className="max-w-4xl mx-auto rounded-xl border border-brand-border bg-brand-surface p-8">
      {demoCards.map((card) => (
        <div
          key={card.id}
          style={{
            animation: animate ? `fadeSlideIn 0.5s ease-out ${card.delay} both` : "none",
            opacity: animate ? undefined : 0,
          }}
          className="bg-brand-bg border border-brand-border rounded-xl p-6 mb-4"
        >
          {/* card content — see UI-SPEC §Card Structure */}
        </div>
      ))}
    </div>
  );
}
```

Note: setting initial `opacity: 0` before the observer fires prevents the flash-of-final-state during hydration.

### Pattern 5: Streamlit branded header (UI-03 + UI-05)

**What:** Replace `st.title` + `st.write` with a single `st.markdown(HEADER_HTML, unsafe_allow_html=True)` call. The HTML is provided verbatim in UI-SPEC §Streamlit Polish.

**When to use:** Once, at the top of the main content area in `app.py`, after `st.set_page_config` and the font `<link>` markdown block.

**Example (verbatim from UI-SPEC):**

```python
# app.py — replace lines 60-61
BRANDED_HEADER_HTML = """
<div style="
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 16px 0;
  border-bottom: 1px solid #e6e9ef;
  margin-bottom: 20px;
  font-family: 'IBM Plex Sans', sans-serif;
">
  <div>
    <span style="font-size: 22px; font-weight: 600; color: #262730;">⚡ Performance Plus</span>
    <span style="display: block; font-size: 14px; font-weight: 400; color: #808495; margin-top: 2px;">
      AI-powered budget decisions from your CRM notes
    </span>
  </div>
  <a href="/" target="_self" style="font-size: 13px; font-weight: 400; color: #808495; text-decoration: none;">
    ← Back to site
  </a>
</div>
"""
st.markdown(BRANDED_HEADER_HTML, unsafe_allow_html=True)
```

### Pattern 6: Streamlit `st.expander` loop with badge inside body (UI-04)

**What:** `st.expander` label cannot render HTML. Workaround: plain-text label outside, badge HTML rendered as the first line inside the expander body.

**When to use:** In place of the current `build_results_table_html` call in `app.py` line 140.

**Example:**

```python
# app.py — replace line 140
from ui_helpers import _badge_html, _pct_html  # both already exist

st.subheader("Campaign Budget Actions")
for c in result.campaigns:
    pct_display = f"+{c.percentage_change}%" if c.percentage_change > 0 else f"{c.percentage_change}%"
    label = f"{c.campaign_id} — {c.budget_action.upper()} {pct_display}"
    with st.expander(label, expanded=False):
        # Badge HTML rendered inside the body since labels don't support HTML
        st.markdown(
            f"{_badge_html(c.budget_action)}  &nbsp;  {_pct_html(c.percentage_change)}",
            unsafe_allow_html=True,
        )
        st.write(c.semantic_reasoning)
        st.caption(
            f"Confidence: {round(c.confidence * 100)}%  ·  "
            f"Sessions analysed: {c.evidence_count}"
        )
```

### Recommended Project Structure

```
performance_plus/
├── app.py                       # MODIFIED — branded header + expander loop
├── ui_helpers.py                # UNCHANGED — _badge_html and _pct_html reused
├── pyproject.toml               # UNCHANGED
├── landing/                     # NEW — Next.js app
│   ├── app/
│   │   ├── layout.tsx           # NEW — next/font/google, html metadata
│   │   ├── page.tsx             # NEW — composes all sections
│   │   ├── globals.css          # NEW — @import tailwindcss + @theme tokens + @keyframes
│   │   └── favicon.ico          # default from create-next-app
│   ├── components/
│   │   ├── HeroSection.tsx      # NEW — "use client"; product name + CTAs + WaitlistForm
│   │   ├── WaitlistForm.tsx     # NEW (optional split) — "use client"; useState + fetch
│   │   ├── HowItWorksSection.tsx# NEW — 3-step grid, server component
│   │   ├── DemoAnimation.tsx    # NEW — "use client"; IntersectionObserver + keyframes
│   │   ├── FeaturesSection.tsx  # NEW — 4-card grid w/ Heroicons
│   │   └── Footer.tsx           # NEW — copyright line
│   ├── postcss.config.mjs       # NEW (auto by create-next-app)
│   ├── next.config.ts           # NEW (auto by create-next-app); leave empty for Phase 7
│   ├── tsconfig.json            # NEW (auto)
│   ├── package.json             # NEW (auto)
│   ├── package-lock.json        # NEW (auto) — commit this
│   ├── eslint.config.mjs        # NEW (auto)
│   ├── .gitignore               # NEW (auto) — already covers node_modules/, .next/, .env.local
│   ├── .env.example             # NEW — document NEXT_PUBLIC_API_BASE_URL
│   └── .env.local               # NEW — local dev only; gitignored
└── .env.example                 # UNCHANGED in Phase 7 (Streamlit-side env unchanged)
```

### Anti-Patterns to Avoid

- **Do not create a `tailwind.config.ts` in `landing/`.** Tailwind v4's default is CSS-first config. Putting custom colors in JS will require an `@config` directive and double-maintenance.
- **Do not render badge HTML in `st.expander(label=...)`.** Streamlit will unwrap or escape it. Always render badge HTML inside the expander body.
- **Do not call `unsafe_allow_html=True` with any user-supplied string** (e.g., `campaign.semantic_reasoning` if it ever came from user input). For Phase 7 the reasoning string comes from a Pydantic-validated LLM response — developer-controlled. Stay disciplined.
- **Do not bake the production API URL into `NEXT_PUBLIC_API_BASE_URL` at build time.** Leave it unset in prod and rely on Caddy same-origin routing (`/api/waitlist`). This is the UI-SPEC's prescribed approach.
- **Do not add `"use client"` to `app/page.tsx` or `app/layout.tsx`.** Keep them Server Components; only Hero, WaitlistForm, and DemoAnimation need `"use client"`.
- **Do not pre-load campaign data from the FastAPI in the landing page.** UI-SPEC mandates hardcoded demo cards — no network call, no flake risk during demo.
- **Do not delete `build_results_table_html` from `ui_helpers.py`** until you've grepped tests for any direct import. (Likely safe to leave; cheap to keep.)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Custom font loader with `<link rel="stylesheet">` | Manual Google Fonts link tag | `next/font/google` | Zero layout shift, self-hosted at build, no runtime Google CDN dependency. Streamlit can keep its `<link>` (different runtime, different constraints). |
| Scroll-triggered animation library | Adding `framer-motion`, `gsap`, `aos.js` | Native `IntersectionObserver` + CSS `@keyframes` | UI-SPEC forbids it; native API is ~5 lines of useEffect; bundle stays minimal. |
| HTML-escaping campaign labels manually | Custom sanitizer in Streamlit | Trust Pydantic-validated LLM output as the developer-controlled source. Don't accept user-supplied campaign strings. | The data comes from `AnalysisResult.campaigns[i].campaign_id` — a frozen synthetic ID. No untrusted user input enters the badge HTML path. |
| Custom email-validation regex for the waitlist input | A `validateEmail()` function in `WaitlistForm.tsx` | `<input type="email" required>` + browser-native validation + Pydantic `EmailStr` on the server (already in Phase 6) | Browser email validation handles 95% of cases; the FastAPI side is the source of truth (returns 422 on malformed). Don't double-validate; trust the server's `EmailStr`. |
| Tailwind config in `tailwind.config.ts` (v3 pattern) | Translating UI-SPEC's TypeScript color block to JS | `@theme { ... }` block in `globals.css` | Tailwind v4 default; auto-discovers CSS-first config. Keep one source of truth. |
| State machine library for form (XState, Zustand) | Adding any state library | `useState<"idle" \| "submitting" \| "success" \| "duplicate" \| "error">` | Five states, one component — vanilla useState is the right tool. |
| Custom badge-rendering React component for Next.js | A new TypeScript Badge component with its own color logic | A shared `BADGE_COLORS` const in `landing/components/badge-tokens.ts` that mirrors `ui_helpers.py` exactly | UI-SPEC locks the same 4 colors + same inline style on both surfaces. One const lookup, no abstraction. |

**Key insight:** This phase is a UI assembly job, not a systems job. Every "could I add a library for this?" should be answered "no — write the 10-line component." The animated demo, the form state, the typography wiring — all are deliberately tiny by spec.

## Runtime State Inventory

> Phase 7 is greenfield (new `landing/` directory) plus surgical edits to `app.py`. No data migration, no service config changes, no OS state. This section is included for completeness because `app.py` is being edited — but every category is verifiably empty.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None.** Phase 7 does not touch Postgres tables. The waitlist table from Phase 6 keeps its same schema. The landing page form just calls the existing `/api/waitlist` endpoint. | None |
| Live service config | **None.** No n8n workflows, no Datadog/Cloudflare/Tailscale resources reference Phase 7 strings. Verified by grep across `compose.yaml`, `caddy/Caddyfile`, `.env.example` — none mention "landing" or "Performance Plus" branding strings. | None |
| OS-registered state | **None.** No Windows Task Scheduler entries, no launchd, no pm2 processes — this is Docker-only deployment. | None |
| Secrets / env vars | `NEXT_PUBLIC_API_BASE_URL` is **new** but is a Next.js build-time var inside `landing/`, not a runtime container env. **Action:** document in `landing/.env.example` (new file). The optional `SITE_URL` for Streamlit's "Back to site" link is hardcoded `/` per UI-SPEC and does NOT require a new env var. No change to project-root `.env.example`. | Add `landing/.env.example` |
| Build artifacts / installed packages | `app.py` change does not affect the existing Streamlit Docker image's build output beyond the .py source file itself. **`ui_helpers.py` is untouched** — no stale .pyc concerns. The `build_results_table_html` function becomes unused but is harmless to leave (cheap insurance). Phase 8 will build a new Next.js Docker image; Phase 7 does NOT. | None for Phase 7 |

**The canonical question** — *After every file is updated, what runtime systems still have the old string cached, stored, or registered?* — **answer: nothing.** This phase adds a new directory and edits two functions in one Python file. No live system reaches back to query Phase 7's surfaces.

## Common Pitfalls

### Pitfall 1: Tailwind v4 ignores `tailwind.config.ts` colors silently

**What goes wrong:** Engineer pastes the UI-SPEC's `tailwind.config.ts` block into the project. Build succeeds. Page renders. But `bg-brand-bg` resolves to the default (no background), because Tailwind v4 doesn't auto-discover JS config.

**Why it happens:** Tailwind v4's CSS engine replaces the v3 PostCSS plugin. Auto-detection of `tailwind.config.{js,ts}` was removed; you must either use `@theme` in CSS (preferred) or explicitly `@config "./tailwind.config.ts"` (legacy).

**How to avoid:** Use the `@theme` block in `globals.css` shown in Pattern 1. Do not create a `tailwind.config.ts` file at all.

**Warning signs:** Custom color utility classes (`bg-brand-bg`, `text-badge-increase`) appear in DevTools but resolve to nothing. Default Tailwind classes (`bg-blue-500`) work fine.

[VERIFIED: tailwindcss.com/docs/upgrade-guide]

### Pitfall 2: `st.expander` label silently drops HTML

**What goes wrong:** Engineer writes `st.expander(f"{badge_html} {campaign_id}")`. The badge HTML appears as escaped text or is unwrapped entirely.

**Why it happens:** `st.expander` label only supports a narrow markdown subset: **bold, italics, strikethrough, inline code, links, images**. HTML and color directives are not in that list. Unsupported markdown is unwrapped to plain text.

**How to avoid:** Plain-text label outside. Badge HTML inside the expander body via `st.markdown(badge_html, unsafe_allow_html=True)`. See Pattern 6.

**Warning signs:** Expander headers show `<span style=...>INCREASE</span>` as literal text, or just the word INCREASE in default font.

[VERIFIED: docs.streamlit.io/develop/api-reference/layout/st.expander]

### Pitfall 3: `NEXT_PUBLIC_*` env var baked into the production image

**What goes wrong:** Engineer sets `NEXT_PUBLIC_API_BASE_URL=https://prod.example.com` at Docker `RUN` time, builds the image, then deploys to a new domain. The old URL is hardcoded in the JS bundle; the new env has no effect.

**Why it happens:** Next.js inlines `NEXT_PUBLIC_*` literals into the client bundle during `next build`. Runtime env vars on the client side are impossible without explicit window-injection hacks.

**How to avoid:** **Leave `NEXT_PUBLIC_API_BASE_URL` unset in production.** The fetch URL becomes `/api/waitlist` (relative path), which Caddy proxies to FastAPI from the same origin. The env var exists only for local dev where the Next.js port (3000) differs from the FastAPI port (8000).

**Warning signs:** The waitlist form 404s in production. DevTools Network tab shows the request going to a hardcoded localhost or stale URL.

[VERIFIED: github.com/vercel/next.js/discussions/87229]

### Pitfall 4: Demo animation plays before user scrolls (defeats the "AI generating" feeling)

**What goes wrong:** All four campaign cards fade in immediately on page load — by the time the user scrolls down, the animation is already done.

**Why it happens:** CSS `@keyframes` start at render time by default. No gating.

**How to avoid:** Use `IntersectionObserver` to set a state flag that switches `animation-play-state` (or, simpler: applies the `animation:` shorthand only when `animate === true`). Set initial `opacity: 0` so cards don't flash on hydration. See Pattern 4.

**Warning signs:** Recording a screencast shows cards already faded in by frame 1; user testers say "I missed the animation."

### Pitfall 5: Hydration mismatch on `WaitlistForm`

**What goes wrong:** Next.js SSRs the form with default state, then hydration adds `useState` — but if the server-rendered HTML differs from the client's initial render, React throws "Hydration failed."

**Why it happens:** Reading `process.env.NEXT_PUBLIC_*` inside a Client Component's render is safe (it's a literal at build time). But conditional rendering based on `typeof window !== "undefined"` differences will break hydration.

**How to avoid:** Use stable initial state (`useState<Status>("idle")`). Don't branch on `window` during render — only inside `useEffect`. The Pattern 3 code does this correctly.

**Warning signs:** Browser console: "Hydration failed because the server rendered HTML didn't match the client."

### Pitfall 6: Streamlit branded header collides with `st.set_page_config` order

**What goes wrong:** `st.set_page_config(...)` must be the **first** Streamlit call. If `st.markdown(BRANDED_HEADER_HTML, ...)` is placed above it, Streamlit raises `StreamlitSetPageConfigMustBeFirstCommandError`.

**Why it happens:** Streamlit imposes a strict ordering: `set_page_config` first, then everything else.

**How to avoid:** Keep the existing `st.set_page_config(...)` call at the top of `app.py`. Insert the branded header markdown **after** `set_page_config` and after the font `<link>` markdown (currently lines 24-27), but **before** any other content. Look at lines 60-61 — that's where the branded header replaces `st.title` + `st.write`.

**Warning signs:** App crashes on load with `StreamlitSetPageConfigMustBeFirstCommandError`.

### Pitfall 7: CORS preflight blocks local dev waitlist POST

**What goes wrong:** Engineer runs Next.js on `localhost:3000` and FastAPI on `localhost:8000`. The browser issues an OPTIONS preflight before the POST. If CORS isn't configured, the preflight fails and the POST never fires.

**Why it happens:** Cross-origin POST with `Content-Type: application/json` triggers a preflight under standard CORS rules.

**How to avoid:** **Already handled** — Phase 6 added `CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])` in `api/main.py` line 33. Verify FastAPI is running locally before testing the form.

**Warning signs:** DevTools Network tab shows a 405/blocked OPTIONS request. Form submission silently fails. (If you see this, restart the FastAPI container and confirm the CORS middleware line is present.)

[VERIFIED: api/main.py line 33]

### Pitfall 8: Heroicons import path mistakes

**What goes wrong:** Engineer writes `import { BoltIcon } from "@heroicons/react"`. Build error: no default export.

**Why it happens:** `@heroicons/react` v2 requires size-and-style-suffixed import paths: `@heroicons/react/24/outline`, `@heroicons/react/24/solid`, `@heroicons/react/20/solid`, `@heroicons/react/16/solid`.

**How to avoid:** `import { BoltIcon, ChartBarIcon, ... } from "@heroicons/react/24/outline";` (matches the spec's 24px icon size).

**Warning signs:** Build error: `Module not found: Can't resolve '@heroicons/react'`.

[VERIFIED: github.com/tailwindlabs/heroicons/tree/master/react]

### Pitfall 9: `app.py` keeps a stale import after refactor

**What goes wrong:** After replacing `build_results_table_html(result)` with the expander loop, `app.py` still has `from ui_helpers import build_results_table_html, build_exec_summary_html` at the top. `ruff` flags `build_results_table_html` as unused. CI fails on lint.

**Why it happens:** `build_exec_summary_html` IS still used (line 138 in the current `app.py`). Only `build_results_table_html` becomes unused. The shared import statement makes this easy to miss.

**How to avoid:** Update the import to `from ui_helpers import build_exec_summary_html, _badge_html, _pct_html` (or whichever helpers the expander loop needs). Run `ruff check app.py` after the edit.

**Warning signs:** `ruff` reports `F401 'ui_helpers.build_results_table_html' imported but unused`.

## Code Examples

> All code examples are provided in the Architecture Patterns section above (Patterns 1-6). The code references the UI-SPEC §Copywriting Contract for exact text strings and §Color System for exact hex values — those are LOCKED and must not be paraphrased.

### Quick-reference: file checklist for the Streamlit polish (UI-03, UI-04, UI-05)

```python
# app.py — minimal diff summary

# 1. Add module-level constant near the top (after imports)
BRANDED_HEADER_HTML = """..."""  # full HTML from UI-SPEC §Streamlit Polish

# 2. Replace lines 60-61
# OLD:
# st.title("Performance Plus")
# st.write("Autonomous Semantic Attribution Engine")
# NEW:
st.markdown(BRANDED_HEADER_HTML, unsafe_allow_html=True)

# 3. Replace line 140
# OLD:
# st.markdown(build_results_table_html(result), unsafe_allow_html=True)
# NEW: expander loop (see Pattern 6)

# 4. Fix the import line at the top
# OLD:
# from ui_helpers import build_results_table_html, build_exec_summary_html
# NEW:
from ui_helpers import build_exec_summary_html, _badge_html, _pct_html
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Next.js Pages Router | App Router (Server Components by default) | Next.js 13 (Oct 2022) — default since 14 | Phase 7 must use `app/` not `pages/`. `create-next-app --app` (or default) handles this. |
| Tailwind CSS v3 with `tailwind.config.ts` | Tailwind CSS v4 with `@theme` in CSS | Tailwind v4 (early 2025) — default since `create-next-app` ~15.2 | UI-SPEC's `tailwind.config.ts` snippet must be ported to `globals.css` `@theme` block. Both versions still work, but v4 is the create-next-app default. |
| `<link href="googleapis.com">` font loading | `next/font/google` self-hosted | Next.js 13 (`next/font` released) — STABLE since 14 | Eliminates FOUT and runtime Google CDN dependency. Phase 7 Next.js side uses `next/font/google`; Streamlit side keeps `<link>` (different runtime). |
| `pages/api/*` route handlers in same Next.js | Separate FastAPI service (already shipped in Phase 5) | This project — Phase 5 | Phase 7 Next.js is **pure frontend**. All backend logic in FastAPI. |
| framer-motion / aos.js for scroll animation | `IntersectionObserver` + CSS `@keyframes` | Browser baseline — IntersectionObserver in all evergreen browsers since 2017 | Smaller bundle, native API, UI-SPEC mandates this. |
| `npm install` + manual `requirements.txt` | `uv` for Python; `create-next-app` defaults for Node | Project-mandated (uv); Next.js 14+ defaults | Phase 7 uses `npx create-next-app` (Node side) and untouched `pyproject.toml` (Python side — no new deps). |
| `st.title()` + `st.write()` | `st.markdown(unsafe_allow_html=True)` for branded headers | Streamlit 1.x baseline | The pattern is unchanged; the choice is intentional — Streamlit's `st.title` cannot do horizontal layouts with a right-aligned link. |

**Deprecated / outdated:**
- **Tailwind v3 `tailwind.config.ts` JS config** — still works in v4 via `@config` directive, but the v4 default and recommended pattern is CSS-first. **Don't use** unless porting an existing v3 project.
- **`response_format={"type": "json_object"}` JSON mode** — irrelevant to Phase 7 (no LLM calls in this phase), noted only for completeness with CLAUDE.md.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The existing tests do not directly import `build_results_table_html` — leaving it as dead code is safe. | Common Pitfalls §Pitfall 9 + Component Responsibilities (Streamlit) | LOW. Worst case: dead-code lint warning; trivial to remove. **Planner should verify** with `grep -r build_results_table_html tests/` during planning. |
| A2 | The FastAPI `/api/waitlist` response on success includes the exact message `"You're on the waitlist! We'll be in touch."` OR the Next.js form should hardcode this string and not parse the response body. | Pattern 3 (WaitlistForm) | LOW. UI-SPEC D-10 says "exact string from the API response" — but in Pattern 3 the React code hardcodes the string and switches on `res.ok`. **Decision needed at plan time:** parse `res.json()` and display `data.message`, OR hardcode the string matching the API's known response. The current `api/main.py` response shape needs confirmation. |
| A3 | The exec summary's pink left-border style (`build_exec_summary_html`) remains visually compatible with the new branded header. | Architecture Patterns §Pattern 5 + Component Responsibilities | LOW. Both use `#f63366` accent — colors match. Visual confirmation needed in human verification step. |
| A4 | The `landing/` directory will NOT be excluded by the current `.dockerignore` in a way that blocks Phase 8's Next.js Docker stage. | Project Constraints (CLAUDE.md) | LOW. The current `.dockerignore` is Streamlit-specific (excludes `tests/`, `*.md`, `design/`, `.planning/`). Phase 7 doesn't need to modify `.dockerignore`; Phase 8 will likely add a separate Dockerfile for Next.js. **Flag for Phase 8 planner**: ensure `landing/node_modules` is excluded but `landing/app` is included in the Next.js build context. |
| A5 | `@heroicons/react` import path `@heroicons/react/24/outline` will tree-shake correctly with Next.js 16 / Turbopack. | Standard Stack (Supporting) | LOW. Heroicons docs explicitly support tree-shaking; Next.js 16 default Turbopack supports tree-shaking. If a regression occurs, swap to inline SVG (UI-SPEC permits). |
| A6 | The FastAPI service at `http://localhost:8000` is running during local Next.js dev, OR the engineer is OK with the form returning a network error during local UI testing. | Pitfall 7 | LOW. Plan should include a "how to test locally" note: start FastAPI first (`uvicorn api.main:app --reload`), then start Next.js (`cd landing && npm run dev`). |

## Open Questions

1. **Should `build_results_table_html` be deleted from `ui_helpers.py` in Phase 7?**
   - What we know: It will become unused after UI-04. Tests in `tests/` are visible but their imports haven't been checked here.
   - What's unclear: Whether any test imports the function directly.
   - Recommendation: Planner runs `grep -rn build_results_table_html tests/` during planning. If zero hits → safe to delete in a separate "tidy" task. If any hits → leave it (cost: a few lines of dead code; benefit: no test churn).

2. **Should the WaitlistForm extract into its own component, or live inline in HeroSection?**
   - What we know: UI-SPEC §Page Structure lists HeroSection but not WaitlistForm as a separate file.
   - What's unclear: Whether the planner prefers component-per-concern (testability) or grouped-by-section (matches UI-SPEC layout exactly).
   - Recommendation: Extract `WaitlistForm.tsx` as a separate file — under 80 lines, easier to reason about state machine, easier to unit-test if testing is added later. Mark HeroSection as `"use client"` only if it also needs interactivity; otherwise HeroSection stays Server Component and the form is the only `"use client"` island.

3. **Does the Streamlit "Back to site" anchor's `href="/"` work in local dev (no Caddy)?**
   - What we know: Local Streamlit runs on `http://localhost:8501`. `href="/"` resolves to `http://localhost:8501/`, which is the Streamlit app itself — a no-op refresh.
   - What's unclear: Whether the demo team accepts this trade-off (link is functional in production via Caddy, no-op locally) or wants a conditional URL.
   - Recommendation: Accept the trade-off. Phase 7 is code-only; Phase 8 wires the routing. Add a code comment near the header HTML: `# href="/" → Caddy routes to Next.js landing in production; no-op refresh in local dev`. Do not add a conditional based on env var — it adds complexity for a hackathon-level concern.

4. **Should `landing/next.config.ts` include `output: "standalone"` now or in Phase 8?**
   - What we know: Phase 8 is explicitly the infra phase per CONTEXT.md and ROADMAP.md.
   - What's unclear: Whether enabling `output: "standalone"` early is harmless (it is — it only affects `next build`).
   - Recommendation: **Leave it out of Phase 7.** Phase 7 is "code only, no Caddy/Docker changes." `next.config.ts` ships from `create-next-app` empty; Phase 8 will add `output: "standalone"` along with the Next.js Dockerfile.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `node` | `create-next-app`, `npm install`, `next dev`, `next build` | ✓ | v25.3.0 (well above Next.js 16's `>=18.18` requirement) | — |
| `npm` | Dependency installation in `landing/` | ✓ | 11.7.0 | `pnpm` or `bun` are alternatives but UI-SPEC implies npm |
| `python` (`>=3.11`) | Streamlit polish edits to `app.py` | ✓ (assumed — Streamlit already running) | 3.11.x | — |
| `uv` | (not needed for Phase 7 — no new Python deps) | ✓ (assumed) | — | — |
| FastAPI at `http://localhost:8000` during local UI testing | Pattern 3 WaitlistForm fetch | ✓ (Phase 5 + 6 shipped) | — | Test with a stubbed fetch or `curl http://localhost:8000/api/health` before testing the form |
| Postgres at `postgres:5432` (Docker network) for local FastAPI | Phase 6 endpoint requires `insert_waitlist_email` to write to DB | ✓ (Phase 5 + 6 shipped via `compose.yaml`) | postgres:16-alpine | — |
| SMTP credentials (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`) | Phase 6 `send_waitlist_notification` — fires on every waitlist signup | Status unknown (env vars in `.env`, not visible to research) | — | If SMTP isn't configured, local form submissions will return 500. Engineer can mock or skip the email step during local UI testing. |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None (SMTP is the only conditional — its absence affects only the 500-error path during local testing, which is fine because Phase 7 only needs to verify the 200/409/error UI states render correctly).

## Validation Architecture

> Skipped — `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json` (line 19).

[VERIFIED: .planning/config.json line 19 — `"nyquist_validation": false`]

## Security Domain

> Required — `workflow.security_enforcement` is `true` in `.planning/config.json` line 42, ASVS Level 1.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | **No** | Waitlist endpoint is public by design (D-12 from Phase 6); landing page has no login. |
| V3 Session Management | **No** | No server-side sessions in Phase 7. Next.js page is stateless; Streamlit's session state is unchanged. |
| V4 Access Control | **No** | No protected resources introduced in Phase 7. |
| V5 Input Validation | **Yes** | Waitlist email validation. Browser `<input type="email" required>` for UX. **Authoritative validation lives in FastAPI's `WaitlistRequest` Pydantic model with `EmailStr`** (already shipped in Phase 6) — returns 422 on invalid input. Do NOT duplicate validation in Next.js with a custom regex (Don't Hand-Roll). |
| V6 Cryptography | **No** | No new crypto in Phase 7. HTTPS is provided by Caddy at the edge (already configured in Phase 4). |
| V14 Configuration | **Yes** | `unsafe_allow_html=True` in Streamlit is in use. **Control:** only render developer-controlled strings (Pydantic-validated LLM output, hardcoded HTML constants). Never interpolate user-submitted strings into the markdown body. Phase 7 maintains this discipline — no user input reaches an `unsafe_allow_html` path. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via `unsafe_allow_html` in Streamlit | Tampering / Information Disclosure | Only render trusted strings. Phase 7's expander body renders `c.semantic_reasoning` (Pydantic-validated LLM string), `_badge_html()` (developer-controlled), and `_pct_html()` (developer-controlled, integer input). All inputs are non-user-controlled. **Verified safe.** |
| XSS via React (Next.js) | Tampering / Information Disclosure | React auto-escapes string children by default. No `dangerouslySetInnerHTML` is needed in Phase 7. **Verified safe.** |
| CSRF on waitlist endpoint | Spoofing | Endpoint is public, idempotent on the user's intent (creating a waitlist record). FastAPI returns 409 on duplicate — no destructive side effects. Standard Same-Origin Policy + same-origin production routing under Caddy mitigates accidental cross-origin POSTs. No additional CSRF token needed for v2.0. |
| Email enumeration via 409 response | Information Disclosure | Returning 409 confirms an email is on the waitlist. **Trade-off:** UX clarity ("you're already on the waitlist") vs. enumeration risk. For a hackathon-stage waitlist, the UX win is preferred. Document as accepted risk; revisit if a paid product is launched. |
| Cross-origin abuse via `allow_origins=["*"]` | Tampering | The waitlist endpoint is public and idempotent. Wildcard CORS is acceptable for v2.0; tighten to specific allowlist when adding authenticated endpoints. [VERIFIED: api/main.py line 33] |
| Sensitive data in Next.js bundle | Information Disclosure | **`NEXT_PUBLIC_*` env vars are inlined into the JS bundle.** Only put non-secret values in vars prefixed `NEXT_PUBLIC_`. `NEXT_PUBLIC_API_BASE_URL` is a public URL — safe. Never expose API keys, DB URLs, or SMTP creds via `NEXT_PUBLIC_`. |

**No new security controls required for Phase 7.** Existing Phase 5-6 controls (API key on protected endpoints, Pydantic input validation, CORS, EmailStr validation) cover everything Phase 7 touches.

## Sources

### Primary (HIGH confidence)

- **Next.js Documentation — create-next-app CLI** — nextjs.org/docs/app/api-reference/cli/create-next-app, lastUpdated 2026-05-31, version 16.2.6. Verified all CLI flags, defaults (TS + ESLint + Tailwind v4 + App Router + Turbopack), `--yes` behavior.
- **Next.js Documentation — output: 'standalone'** — nextjs.org/docs/app/api-reference/config/next-config-js/output. Used to confirm Phase 8 boundary; Phase 7 leaves `next.config.ts` empty.
- **Tailwind CSS Upgrade Guide** — tailwindcss.com/docs/upgrade-guide. Verified `@theme` directive replaces `tailwind.config.ts`; JS config still works via `@config` but is legacy.
- **Streamlit Docs — st.expander** — docs.streamlit.io/develop/api-reference/layout/st.expander. Verified label supports only bold/italics/strikethrough/inline code/links/images. **No HTML.** No color directives.
- **Streamlit Docs — st.badge** — docs.streamlit.io/develop/api-reference/text/st.badge. Verified colors (red/orange/yellow/blue/green/violet/gray/primary) and that the badge directive works "everywhere Streamlit supports Markdown" — but `st.expander` label does NOT support color directives per the expander docs.
- **Heroicons GitHub README** — github.com/tailwindlabs/heroicons/tree/master/react. Verified import path requirements, MIT license, tree-shaking support.
- **npm registry verification** (current as of 2026-06-01):
  - `npm view next version` → 16.2.6
  - `npm view react version` → 19.2.6
  - `npm view tailwindcss version` → 4.3.0
  - `npm view @heroicons/react version` → 2.2.0
  - `npm view typescript version` → 6.0.3
- **Project files (verified by reading)**:
  - `./CLAUDE.md` (full stack constraints)
  - `./app.py` (current 141 lines — line numbers cited)
  - `./ui_helpers.py` (badge color constants confirmed identical to UI-SPEC)
  - `./pyproject.toml` (Python deps unchanged for Phase 7)
  - `./compose.yaml` (Phase 8 will modify, Phase 7 does not)
  - `./caddy/Caddyfile` (Phase 8 will modify, Phase 7 does not)
  - `./api/main.py` lines 33, 78-93 (CORSMiddleware + waitlist endpoint shipped in Phase 6)
  - `.planning/config.json` (security_enforcement: true, nyquist_validation: false)
  - `.planning/phases/07-landing-page-ui-polish/07-CONTEXT.md` and `07-UI-SPEC.md` (decisions + design contract)
  - `.planning/REQUIREMENTS.md` (LAND-01–04, UI-03–05 traceability)
  - `.planning/STATE.md` (Phase 6 decisions, CORS already enabled)
  - `.planning/ROADMAP.md` (Phase 7 success criteria, Phase 8 scope boundary)

### Secondary (MEDIUM confidence)

- **owolf.com — Next.js 15 + Tailwind 4 font wiring** — confirms the `@theme inline` pattern for mapping `next/font/google` CSS variables into Tailwind utility classes.
- **designrevision.com — Tailwind + Next.js Setup Guide 2026** — confirms PostCSS plugin requirement (`@tailwindcss/postcss`) for Next.js + Tailwind v4.
- **medium.com (Chris Gustin) — Animate on scroll with IntersectionObserver** — pattern reference for `animation-play-state` gating.
- **vercel/next.js Discussion #87229 — Runtime env vars in Next.js** — confirms `NEXT_PUBLIC_*` bake-at-build-time behavior; informs the "leave unset in production" strategy.

### Tertiary (LOW confidence — none used as authoritative)

- General "best practice" articles for React form handling — used only for cross-checking the UI-SPEC-prescribed `useState`-driven pattern. No claims in this research are sourced solely from these.

## Metadata

**Confidence breakdown:**

- **Standard stack:** HIGH — all versions verified against npm registry on 2026-06-01; Next.js, Tailwind, React, Heroicons, TypeScript all cross-checked.
- **Architecture (Tailwind v4 vs v3 implications):** HIGH — multiple authoritative sources (Tailwind upgrade guide + Next.js install docs) agree on the v4 default and the `@theme` pattern. UI-SPEC's `tailwind.config.ts` block requires translation, called out explicitly.
- **Streamlit polish patterns:** HIGH — `st.expander` HTML limitation documented in current Streamlit docs; UI-SPEC already prescribes the workaround. Existing code (`app.py`, `ui_helpers.py`) read line-by-line.
- **Pitfalls:** HIGH — all 9 pitfalls are either documented in official sources (Pitfalls 1, 2, 3, 6, 7, 8) or directly verified in code (Pitfalls 5, 9) or are standard browser/CSS knowledge (Pitfall 4).
- **Cross-stack integration (CORS, env vars):** HIGH — Phase 6's CORS middleware verified in `api/main.py`; `NEXT_PUBLIC_*` build-time behavior verified in Next.js discussions.

**Research date:** 2026-06-01
**Valid until:** ~2026-07-01 (30 days — Next.js minor releases happen monthly; Tailwind v4 is stable; Streamlit changes are additive). Re-verify if planning is delayed past 2026-07-01.
