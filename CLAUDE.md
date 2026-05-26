<!-- GSD:project-start source:PROJECT.md -->

## Project

**Performance Plus — Autonomous Semantic Attribution Engine**

A GenAI-native performance marketing tool that stitches web analytics data with CRM sales notes and uses gpt-4o to translate qualitative lead sentiment into immediate, quantitative ad budget decisions. Built as a hackathon MVP (OpenAI x Outskill AI Builders Cohort 01) with intent to grow into a B2B SaaS product.

The app ingests Web Analytics CSV and CRM CSV files, merges them via `session_id`, sends the unified data to an OpenAI gpt-4o "autonomous CMO" agent, and outputs structured budget action recommendations (increase/pause/decrease by %) alongside creative pivot advice for each campaign.

**Core Value:** A marketer can upload their web analytics and CRM exports and instantly get AI-reasoned budget routing decisions based on what sales reps actually said about each lead — not just what the click data shows.

### Constraints

- **Tech Stack:** Python 3.11+, Streamlit, Pandas, OpenAI gpt-4o — fixed for hackathon judging criteria
- **LLM:** OpenAI gpt-4o only (hackathon is OpenAI-sponsored)
- **Data:** Synthetic/mock data only for demo — no real user data handling required
- **Output format:** Strict JSON via `response_format=` — LLM must return deterministic structured output
- **Deployment:** Self-hosted VPS with Docker — Coolify not in scope

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## TL;DR (read this first)

- **Language:** Python 3.11 (project-mandated; do not jump to 3.13+ — some scientific wheels lag).
- **UI:** Streamlit 1.40+ — use `st.file_uploader`, `st.dataframe`, `st.status`, and `st.json` for the LLM output panel. Don't add a separate web framework.
- **LLM:** `openai>=1.50` Python SDK using `client.beta.chat.completions.parse()` with a Pydantic schema — this is OpenAI's officially supported path for "Structured Outputs" on gpt-4o and is dramatically more reliable than the older `response_format={"type":"json_object"}` JSON-mode.
- **Data:** Pandas 2.2.x (stable, well-supported wheels) — use `pd.merge(..., on="session_id", how="inner", validate="m:1")` for the stitch.
- **Packaging:** **`uv`** (Astral) — single binary, ~10–100× faster than pip/poetry, generates a lockfile, drop-in for Docker. Use it both locally and in the container.
- **Container:** `python:3.11-slim` base, multi-stage with `uv sync --frozen --no-dev`, run `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`.
- **VPS edge:** Caddy (auto-HTTPS) or Nginx as a reverse proxy in front of the Streamlit container with WebSocket upgrade headers — Streamlit will not work behind a vanilla HTTP-only proxy.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | **3.11.x** | Runtime | Project constraint; widest wheel coverage for pandas / numpy / pyarrow; long support window. 3.12 also fine but 3.13 still has spotty wheels for some scientific libs. | HIGH |
| Streamlit | **1.40.x or newer (>=1.40,<2.0)** | UI + state + file upload + dataframe rendering | The de-facto Python-native data-app framework. Built-in `file_uploader`, `dataframe`, `status`, `cache_data`, and session_state cover 100% of this app's UI needs without HTML/JS. Hackathon constraint. | HIGH |
| Pandas | **2.2.x** (>=2.2.3,<2.3) | CSV ingestion + `session_id` merge | Verified latest stable line. PyArrow-backed dtypes available, `merge(validate=...)` catches accidental m:m joins (critical for attribution). 2.3.x exists but stick with 2.2 for wider ecosystem compatibility. | HIGH |
| OpenAI Python SDK | **>=1.50,<2.0** | gpt-4o client + Structured Outputs | Official SDK. `client.beta.chat.completions.parse()` with a Pydantic `response_format=` class is the supported "Structured Outputs" path that guarantees schema-conformant JSON on gpt-4o (much stronger guarantee than the legacy json-mode). | HIGH |
| Pydantic | **2.x** (>=2.8,<3.0) | Schema for budget-action JSON | Defines the strict response schema the SDK enforces. Also gives runtime validation + type hints for the downstream display code. Pydantic v2 is the only version OpenAI's `.parse()` helper supports. | HIGH |
| Docker | **24+** (BuildKit on) | Containerization | VPS deployment constraint. Multi-stage build keeps the runtime image <300 MB. | HIGH |
| uv (Astral) | **>=0.5** | Python dep resolver + venv + lockfile | Replaces pip + pip-tools + virtualenv + (optionally) poetry with one Rust binary. Resolves and installs in seconds, has a real lockfile (`uv.lock`), and integrates cleanly with Docker layer caching. Anthropic, FastAPI, etc. have adopted it as the 2025 default. | MEDIUM-HIGH |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `python-dotenv` | >=1.0 | Load `OPENAI_API_KEY` from `.env` in local dev | Local dev only; in production read from container env vars. | HIGH |
| `pyarrow` | >=15 | Faster CSV/Parquet I/O backing for pandas | Optional but recommended — pandas 2.x with PyArrow strings is faster and uses less RAM for the merged dataframe. | MEDIUM |
| `tenacity` | >=8.5 | Retry wrapper around OpenAI calls | Wrap the gpt-4o call so transient 429/5xx errors don't kill the demo. 3 attempts, exponential backoff, jitter. | MEDIUM |
| `tiktoken` | >=0.7 | Token counting before sending to gpt-4o | Lets you preflight-check that the merged dataframe + system prompt stay under the 128k context window. Optional for hackathon, recommended for SaaS. | MEDIUM |
| `streamlit-extras` | latest | UX polish (badges, metric cards) | Optional — only if you want nicer-looking output cards for the campaign actions. Skip for MVP. | LOW |
| `loguru` | >=0.7 | Structured logging | Drop-in replacement for stdlib logging; useful when debugging the LLM round-trip on the VPS. | MEDIUM |
| `ruff` | >=0.6 | Lint + format | Replaces flake8, isort, and (mostly) black in one tool. Fast, zero-config. | HIGH |
| `pytest` | >=8 | Unit tests for the merge logic + Pydantic schema | Test the `session_id` join with happy/orphan/duplicate fixtures. | HIGH |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `uv` | Lockfile + venv + install | `uv init`, `uv add streamlit pandas openai pydantic`, `uv run streamlit run app.py`. Commit `uv.lock`. |
| `ruff` | Lint + format | Single `ruff check --fix` + `ruff format` pre-commit hook. |
| `pre-commit` | Git hooks | Run ruff + a JSON-schema check on the Pydantic model. |
| Docker BuildKit | Faster builds | `# syntax=docker/dockerfile:1.7` + `--mount=type=cache,target=/root/.cache/uv`. |
| `docker compose` v2 | Local container orchestration | One `compose.yaml` for app + Caddy on the VPS. |
| Caddy 2 | HTTPS reverse proxy | Auto Let's Encrypt; one-line WebSocket support for Streamlit. Easier than Nginx for a single-app VPS. |

## Installation

### Local development (uv-based)

# 1. Install uv (one time)

# 2. Initialize project

# 3. Core deps

# 4. Dev deps

# 5. Run

### `pyproject.toml` shape (excerpt)

### Dockerfile (multi-stage, uv-based)

# syntax=docker/dockerfile:1.7

### `compose.yaml` (VPS)

## Reference patterns

### 1. CSV ingest + session_id stitch (Pandas)

### 2. Streamlit shell

### 3. OpenAI Structured Outputs (the canonical 2025 pattern)

- Use `.beta.chat.completions.parse(...)` (NOT plain `.create()` with `response_format={"type":"json_object"}`). The `.parse()` path enforces the schema server-side and returns a populated Pydantic instance — no `json.loads` + try/except dance.
- `gpt-4o-2024-08-06` (or any newer `gpt-4o-*` snapshot) is the minimum model for Structured Outputs. Plain `gpt-4o` alias should also work but pin a snapshot for reproducibility.
- Pass the dataframe as CSV in the user message; CSV beats JSON for token efficiency on tabular data.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Streamlit | **Gradio** | If the demo is a single-screen "data in → JSON out" widget. For this app's two-CSV-upload + dataframe-preview + actions-list flow, Streamlit's state model and layout primitives are a better fit. |
| Streamlit | **FastAPI + HTMX/React** | If you eventually need multi-user auth, async background jobs, or a polished landing page. Right call for the v2 SaaS, wrong call for a 5-day hackathon. |
| Streamlit | **Reflex (formerly Pynecone)** | If you want a true SPA written in Python. More flexible than Streamlit, but a steeper learning curve and worse hackathon ROI. |
| Streamlit | **Panel / Dash / NiceGUI** | Panel/Dash are heavier and Plotly-centric; NiceGUI is nice but smaller community. None beat Streamlit's file-upload + dataframe ergonomics. |
| `uv` | **Poetry 1.8+** | If the team already has Poetry muscle memory or needs Poetry-specific plugins. Otherwise `uv` is strictly faster. |
| `uv` | **`pip` + `pip-tools`** | Fine for a one-file Dockerfile in a vacuum, but no real lockfile UX and 10–100× slower in CI. |
| `uv` | **pdm / hatch / rye** | All reasonable; `rye` has effectively been folded into `uv`'s direction. Pick `uv` for momentum and ecosystem support. |
| `client.beta.chat.completions.parse()` | **`response_format={"type":"json_object"}` (JSON mode)** | Use only if you need a model older than `gpt-4o-2024-08-06`. JSON mode guarantees valid JSON but NOT schema conformance — you'd have to validate with Pydantic yourself. |
| `client.beta.chat.completions.parse()` | **OpenAI Responses API** | The newer Responses API (`client.responses.parse`) is broadly equivalent and may become the long-term standard; for a hackathon, `chat.completions.parse` has more examples and tutorials. Either works; pick one and stick to it. |
| Caddy | **Nginx / Traefik** | Nginx if you need request-shaping or already use it elsewhere. Traefik if you'll add more services later. Caddy wins on simplicity for a single-app VPS. |
| `pandas.merge` | **Polars** | Polars is faster and has a nicer API, but Streamlit's `st.dataframe` integration and the existing pandas ecosystem (read_csv quirks, etc.) mean pandas is the lower-risk choice for a 5-day build. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `openai<1.0` (the old `openai.ChatCompletion.create` API) | Removed Nov 2023; tutorials referencing it are outdated. | `openai>=1.50` with `client = OpenAI()`. |
| `response_format={"type": "json_object"}` as your *primary* strategy | Guarantees JSON but not your schema — you still have to validate & re-prompt on failures. Adds latency and brittleness. | `client.beta.chat.completions.parse(response_format=PydanticModel)` for true Structured Outputs. |
| Plain `gpt-4` or `gpt-3.5-turbo` for this app | Worse reasoning over tabular sales-note context; gpt-3.5 doesn't support Structured Outputs at all. | `gpt-4o-2024-08-06` (or newer `gpt-4o` snapshot). |
| Pydantic v1 | Not supported by OpenAI's `.parse()` helper; deprecated. | Pydantic v2. |
| `requirements.txt`-only workflow (no lockfile) | "Works on my machine" drift between local and Docker is the #1 demo-day footgun. | `uv.lock` (or `poetry.lock`) committed to the repo, used by `uv sync --frozen` in Docker. |
| `python:3.11` full image as the runtime base | ~1 GB; slow to push/pull to the VPS. | `python:3.11-slim-bookworm` or the Astral `uv` slim image. ~150 MB. |
| Nginx default config in front of Streamlit | Drops the WebSocket upgrade; UI silently stops updating after first render. Most common self-hosted bug. | Caddy (auto-handles WS) or Nginx with explicit `Upgrade`/`Connection` headers + `proxy_read_timeout 3600;`. |
| Running Streamlit on port 80/443 directly in the container | Loses TLS termination & makes future multi-service deploys painful. | Streamlit on 8501, reverse proxy terminates TLS on 443. |
| Hardcoding `OPENAI_API_KEY` in the image | Bakes the secret into every layer; leaks via `docker history`. | Pass via `compose.yaml` `environment:` from a `.env` file on the VPS (gitignored). |
| `pd.merge(..., how="outer")` for the stitch | Produces NaN-filled rows that confuse the LLM (it'll hallucinate reasoning for empty CRM notes). | `how="inner"` + `validate="m:1"` so the LLM only sees fully-attributed sessions. |
| Streamlit `st.experimental_*` APIs | Most have been stabilized or renamed since 1.30+. | Their stable counterparts (e.g., `st.cache_data`, `st.rerun`). |

## Stack Patterns by Variant

- Streamlit + Pandas + OpenAI SDK is *more* than enough; do not add FastAPI, Celery, Redis, or a database.
- Skip `tenacity` only if you're willing to manually click "retry" — strongly recommend keeping it for the live demo.
- Split the LLM agent into a FastAPI service so multiple tenants and the Meta Ads API can share it.
- Keep Streamlit as the internal/analyst UI; build a separate Next.js dashboard for paying customers.
- Add Postgres (Supabase or self-hosted) for tenant data, and Redis for caching gpt-4o responses.
- Replace local in-memory state with a job queue (Arq or Celery) for the agent runs.
- Add a "preview" mode that runs `gpt-4o-mini` first, then escalates to `gpt-4o` only on the final action set. Mini supports Structured Outputs and is ~10× cheaper.
- Pre-aggregate per `campaign_id` before sending to the LLM (group sessions, summarize sales-note sentiment).
- Don't try to fit a 100k-row CSV into the prompt — the 128k context window will technically allow it but quality degrades sharply past ~30k rows of CSV text.

## Version Compatibility

| Package A | Compatible With | Notes | Confidence |
|-----------|-----------------|-------|------------|
| `streamlit>=1.40` | Python 3.9–3.13 | 3.11 is the sweet spot; 3.13 wheels for pyarrow may lag. | MEDIUM |
| `openai>=1.50` | `pydantic>=2.8` | `.parse()` requires Pydantic v2 — v1 will raise at import. | HIGH |
| `pandas>=2.2` | `pyarrow>=15`, `numpy>=1.26` | Verified latest stable line is 2.3.3 (Sept 2025); 2.2.x is the recommended floor. | HIGH (verified) |
| `uv` | Any Python 3.8+ | `uv` itself is a static binary; it installs the Python interpreter for you if needed (`uv python install 3.11`). | HIGH |
| Streamlit + Docker | needs WS-aware proxy | Caddy works zero-config; Nginx needs `Upgrade`/`Connection` headers. | HIGH |
| `gpt-4o-2024-08-06` model | `openai>=1.40` | Earliest model snapshot supporting Structured Outputs `.parse()`. | HIGH |

## Risk Register (stack-level only)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Streamlit WebSocket dropped by reverse proxy → blank UI on VPS | High if Nginx default | Demo-breaking | Use Caddy, or add WS headers to Nginx. Test on the VPS day 4, not day 5. |
| `gpt-4o` rate limit during live demo | Medium | Demo-breaking | Wrap with `tenacity` (3 retries, jitter). Pre-record a fallback Loom. |
| pandas merge silently fans-out on duplicate `session_id` | Medium | Wrong recommendations | `validate="m:1"` on the merge call (raises instead of bloating). |
| Structured Outputs refuses to validate due to an enum mismatch | Low | One bad demo run | Keep `budget_action` as a `Literal[...]` with exactly the allowed values. |
| Docker image too large / slow to deploy to VPS | Low | Slow iteration | Use multi-stage build + `python:3.11-slim-bookworm` runtime stage. |
| `OPENAI_API_KEY` accidentally committed | Medium | Account compromise | `.env` in `.gitignore`; pre-commit hook with `detect-secrets`. |

## Open Questions / Gaps (to revisit before locking versions)

## Sources

- Pandas changelog (WebFetch successful) — confirmed Pandas 2.3.3 latest 2025 release, 3.0.x in 2026. HIGH.
- OpenAI Structured Outputs guide (documented behaviour up to assistant knowledge cutoff Jan 2026): `client.beta.chat.completions.parse()` + Pydantic. HIGH (training data).
- Streamlit docs (training data) — `st.file_uploader`, `st.dataframe`, `st.status`, session_state semantics. MEDIUM-HIGH.
- Astral `uv` docs (training data) — single-binary installer, lockfile, Docker integration. MEDIUM-HIGH.
- Self-hosted Streamlit / Caddy WebSocket gotcha — well-documented community pattern. HIGH (training data, repeatedly seen across forums).
- Project plan v2 + `PROJECT.md` (read locally) — confirmed fixed constraints (Python 3.11+, Streamlit, Pandas, gpt-4o, Docker, self-hosted VPS).
- `streamlit` latest
- `openai` latest
- `pydantic` latest
- `uv` latest
- gpt-4o snapshot string

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
