# Performance Plus

**Autonomous Semantic Attribution Engine**

Performance Plus stitches web analytics data with CRM sales notes and uses GPT-4o to translate qualitative lead sentiment into immediate, quantitative ad budget decisions.

A marketer uploads their web analytics export and CRM export, and instantly gets AI-reasoned budget routing decisions based on what sales reps actually said about each lead — not just what the click data shows.

**Live demo:** https://agent.rukesh.in

---

## The Problem It Solves

Standard performance marketing dashboards show you clicks, impressions, cost-per-click, and conversion rates. They tell you nothing about what your sales team said when those leads actually picked up the phone.

A campaign can look great on paper — high click-through rate, low CPL — and be full of completely wrong-ICP leads. Conversely, a campaign with modest click metrics might be generating your highest-value pipeline. Without joining the quantitative signal to the qualitative sales notes, your budget routing is blind.

Performance Plus bridges that gap by:

1. Joining web analytics sessions to CRM records on `session_id`
2. Rolling up the merged data to campaign level
3. Sending the unified dataset to GPT-4o as a structured prompt
4. Receiving back a deterministic JSON action plan — `increase`, `decrease`, `pause`, or `insufficient_data` per campaign, with percentage change, confidence score, and reasoning that cites the actual sales-note language

---

## Features

- **One-click demo** — pre-built synthetic data loads instantly, no CSV prep required
- **DEMO_MODE** — full end-to-end flow without an OpenAI API key (cached from a real GPT-4o run)
- **BYOK (Bring Your Own Key)** — paste any OpenAI key in the sidebar to run a live GPT-4o call
- **Structured Outputs** — uses `client.beta.chat.completions.parse()` with Pydantic v2 schema enforcement; the model cannot return a malformed response
- **Color-coded results table** — green (increase), red (pause), yellow (decrease), grey (insufficient data)
- **Executive summary** — 2–3 sentence portfolio health snapshot above the action table
- **Docker-ready** — multi-stage Dockerfile, Caddy reverse proxy config, Compose file included

---

## Quickstart (Local)

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `pip install uv` or `brew install uv`
- An OpenAI API key (only needed for live mode — demo mode works without one)

### 1. Clone and install

```bash
git clone <your-repo-url>
cd performance_plus
uv sync
```

### 2. Set up environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...your-key...   # leave blank to use demo mode only
DEMO_MODE=                          # set to 1 to enable demo mode
```

### 3. Run

```bash
uv run streamlit run app.py
```

Open http://localhost:8501.

---

## Usage Walkthrough

### Demo Mode (no API key required)

The fastest way to see the full flow:

```bash
DEMO_MODE=1 uv run streamlit run app.py
```

1. You'll see a blue banner at the top: **"Running in demo mode — cached results, no live API call"**
2. The sidebar shows a green **"Demo Mode"** badge instead of an API key input
3. Click **Load Demo Data** — 20 sessions across 5 campaigns load from `data/web_analytics.csv` and `data/crm_data.csv`, stitched on `session_id`
4. The **Stitched Dataframe Preview** shows all 9 columns: web analytics + CRM data side by side
5. Click **Run Analysis** — results render within ~1 second (loaded from `data/fixture_results.json`)
6. The **Budget Action Results** table shows one row per campaign with a color-coded badge, percentage change, AI reasoning, confidence score, and session count

### Live Mode (with API key)

For a real GPT-4o call:

```bash
uv run streamlit run app.py
```

1. Paste your `sk-...` key in the **OpenAI API Key** sidebar input
2. Sidebar confirms **"Key set — ready to analyse"**
3. Click **Load Demo Data** → **Run Analysis**
4. GPT-4o analyses the campaigns (~5–15 seconds, ~$0.01–0.05 per run)
5. Results render with fresh AI reasoning

> **Tip:** In `DEMO_MODE=1`, pasting a key in the sidebar switches to live mode automatically. The fixture is a fallback, not a lockout.

---

## Feeding Your Own Data

Performance Plus expects two CSV files joined on `session_id`.

### Web Analytics CSV

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | string | Unique session identifier — foreign key to CRM CSV |
| `campaign_id` | string | Campaign identifier (e.g. `cmp_b2b_search`) |
| `clicks` | integer | Click count for this session |
| `impressions` | integer | Impression count |
| `cost_usd` | float | Spend in USD |
| `conversion_rate` | float | Conversion rate (0.0–1.0) |

Example:
```csv
session_id,campaign_id,clicks,impressions,cost_usd,conversion_rate
sess_001,cmp_b2b_search,142,4800,87.5,0.031
sess_002,cmp_competitor_conquest,38,2100,42.0,0.078
```

### CRM CSV

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | string | Must match the web analytics `session_id` exactly |
| `campaign_id` | string | Must match the web analytics `campaign_id` |
| `lead_status` | string | e.g. `Qualified`, `Disqualified`, `Follow-up` |
| `projected_value` | float | Pipeline value in USD (0.0 if disqualified) |
| `sales_notes` | string | Free-text rep notes — this is what GPT-4o reasons over |

Example:
```csv
session_id,campaign_id,lead_status,projected_value,sales_notes
sess_001,cmp_b2b_search,Disqualified,0.0,Wrong ICP. Looking for SMB tooling not enterprise.
sess_002,cmp_competitor_conquest,Qualified,5000.0,Perfect fit. Ready to sign next week.
```

### How to use your own CSVs

Replace the files in the `data/` directory:

```bash
cp your_web_analytics.csv data/web_analytics.csv
cp your_crm_export.csv data/crm_data.csv
```

Then run the app. The join requires:
- `session_id` values to overlap between the two files (inner join — sessions without a match are dropped)
- `session_id` to be unique in the CRM CSV (one sales rep note per session)
- At least one overlapping session to proceed

> **Note:** The current UI uses `Load Demo Data` which reads from `data/`. If you want file upload support instead of replacing files, that is a planned future feature.

### Regenerating the demo fixture

If you change the demo CSVs and want to update the cached fixture results:

```bash
export OPENAI_API_KEY=sk-...
unset DEMO_MODE
uv run python scripts/generate_fixture.py
```

This runs a real GPT-4o call and writes fresh results to `data/fixture_results.json`.

---

## Understanding the Output

Each campaign gets one row in the results table:

| Column | Description |
|--------|-------------|
| `campaign_id` | Matches the campaign_id from your input |
| `action` | **INCREASE** (green) / **PAUSE** (red) / **DECREASE** (yellow) / **INSUFFICIENT DATA** (grey) |
| `budget_change_%` | Signed percentage: `pause = -100%`, `insufficient_data = 0%` |
| `reasoning` | One sentence from GPT-4o citing specific sales-note language |
| `confidence` | 0–100% — how consistent the qualitative signal is across sessions |
| `sessions` | Number of sessions analysed for this campaign |

**Decision logic GPT-4o follows:**
- Sales-rep notes **override** click volume when they signal clear disqualification or strong qualification
- A campaign with high clicks but all "Disqualified" or "Wrong ICP" notes → **PAUSE**
- A campaign with modest clicks but "Ready to sign", "Perfect fit" notes → **INCREASE**
- Fewer than ~2 sessions with sparse notes → **INSUFFICIENT DATA**

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| UI | Streamlit 1.40+ |
| Data layer | Pandas 2.2 — inner join with `validate="m:1"` on `session_id` |
| AI layer | OpenAI GPT-4o (`gpt-4o-2024-08-06`) via `client.beta.chat.completions.parse()` |
| Schema | Pydantic v2 — server-side Structured Outputs enforcement |
| Retry | Tenacity — 3 attempts, exponential backoff, skips model refusals |
| Packaging | uv (Astral) — lockfile, virtualenv, Docker layer caching |
| Container | Docker multi-stage build, `python:3.11-slim-bookworm`, non-root user |
| Proxy | Caddy 2 (auto-HTTPS, WebSocket support) |

---

## Deployment

The app runs as four Docker services behind a Caddy reverse proxy:

| Service | Image / Build target | Internal port | Public path |
|---------|----------------------|---------------|-------------|
| `landing` | Next.js (`landing/Dockerfile`) | 3000 | `/` (catch-all) |
| `app` | Streamlit (`Dockerfile` → `streamlit` stage) | 8501 | `/app*` |
| `fastapi` | FastAPI (`Dockerfile` → `api` stage) | 8000 | `/api/*` |
| `caddy` | `caddy:2-alpine` | 80 / 443 | TLS termination + routing |
| `postgres` | `postgres:16-alpine` | 5432 | internal only |

---

### Prerequisites

- A VPS with Docker 24+ and Docker Compose v2 installed (`docker compose version`)
- A domain (or subdomain) with an A record pointing at your server's public IP
- Port 80 and 443 open in your firewall / security group
- Git installed on the server

---

### 1. Clone the repo

```bash
git clone https://github.com/24rukesh/performance_plusv2.git
cd performance_plusv2
```

---

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in every value:

```env
# OpenAI — leave blank to force demo mode server-wide
OPENAI_API_KEY=sk-...your-key...

# Set to 1 to serve cached fixture results (no API key needed for visitors)
DEMO_MODE=1

# Internal API key checked by the FastAPI service
API_KEY=generate-a-random-string

# Postgres — used by the FastAPI service
DATABASE_URL=postgresql://ppuser:CHANGE_ME@postgres:5432/performance_plus
POSTGRES_PASSWORD=CHANGE_ME

# SMTP — used by the waitlist endpoint to send notification emails
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASS=your-smtp-password
SMTP_FROM=noreply@yourdomain.com
```

> **Security:** `.env` is in `.gitignore`. Never commit it.

---

### 3. Set your domain in Caddyfile

Open `caddy/Caddyfile` and replace `agent.rukesh.in` with your domain:

```
yourdomain.com {

    handle /api/* {
        reverse_proxy fastapi:8000
    }

    handle_path /app* {
        reverse_proxy app:8501
    }

    handle {
        reverse_proxy landing:3000
    }
}
```

Caddy provisions a Let's Encrypt TLS certificate automatically on first boot — no manual cert work required.

---

### 4. Build and start

```bash
docker compose up -d --build
```

This builds all four images and starts every service. The first build takes 3–5 minutes (dependency installation). Subsequent builds use layer cache and finish in under 60 seconds.

---

### 5. Verify the deployment

```bash
# All five containers should show "Up" or "healthy"
docker compose ps

# Tail Caddy to confirm the TLS cert issued
docker compose logs caddy --tail=50

# Check each service health endpoint
curl https://yourdomain.com/api/health        # → {"status":"ok"}
curl https://yourdomain.com/app/_stcore/health # → "ok"
curl https://yourdomain.com/                   # → Next.js landing HTML
```

---

### 6. Check individual service logs

```bash
docker compose logs app      --tail=100 -f   # Streamlit
docker compose logs fastapi  --tail=100 -f   # FastAPI / waitlist
docker compose logs landing  --tail=100 -f   # Next.js
docker compose logs postgres --tail=100 -f   # Postgres
docker compose logs caddy    --tail=100 -f   # Caddy / TLS
```

---

### Updating after a code change

```bash
git pull origin main
docker compose up -d --build
```

Only the services whose images changed are rebuilt. Caddy and Postgres restart instantly (no rebuild).

---

### Rolling back

```bash
# Find the previous image ID for a service
docker images | grep performance_plusv2

# Restart from a previous image tag (if you tagged before deploying)
docker compose down app
docker compose up -d app
```

For a hard rollback, check out the previous commit and rebuild:

```bash
git checkout <previous-commit-sha>
docker compose up -d --build
```

---

### Stopping / teardown

```bash
# Stop all services (preserves volumes)
docker compose down

# Stop and delete all volumes including the Postgres database
docker compose down -v
```

---

### Environment variable reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No | — | GPT-4o key. Omit to force `DEMO_MODE` globally. |
| `DEMO_MODE` | No | `""` | Set to `1` to serve cached fixture results to all visitors. |
| `API_KEY` | Yes | — | Internal secret the FastAPI service validates on protected routes. |
| `DATABASE_URL` | Yes | — | Full Postgres connection string. Must use the `postgres` service hostname inside Compose. |
| `POSTGRES_PASSWORD` | Yes | — | Postgres password — must match the password in `DATABASE_URL`. |
| `SMTP_HOST` | Yes (waitlist) | — | SMTP server hostname. |
| `SMTP_PORT` | Yes (waitlist) | `587` | SMTP port (587 = STARTTLS, 465 = SSL). |
| `SMTP_USER` | Yes (waitlist) | — | SMTP username / login. |
| `SMTP_PASS` | Yes (waitlist) | — | SMTP password / app password. |
| `SMTP_FROM` | Yes (waitlist) | — | `From:` address for waitlist notification emails. |

---

### Architecture diagram

```
Internet
    │
    ▼
Caddy :443 (TLS)
    ├── /api/*        → FastAPI :8000
    ├── /app*         → Streamlit :8501
    └── /             → Next.js landing :3000
                              │
                         FastAPI :8000
                              │
                         Postgres :5432
```

---

## Running Tests

```bash
# All tests (excludes live integration eval)
uv run pytest tests/ -v --ignore=tests/test_llm_eval.py

# LLM unit tests only
uv run pytest tests/test_llm.py -v

# Deploy config invariant tests
uv run pytest tests/test_deploy_config.py -v
```

Tests cover: data layer merge logic, LLM schema validation, DEMO_MODE intercept behavior, fixture schema, and deploy config invariants (Dockerfile non-root, Compose port topology, Streamlit CORS config).

---

## Project Structure

```
performance_plus/
├── app.py                    # Streamlit UI — main entry point
├── llm.py                    # GPT-4o client, Pydantic schema, run_analysis()
├── data.py                   # CSV ingestion and session_id merge
├── ui_helpers.py             # HTML table and badge rendering
├── data_generator.py         # Synthetic demo data generator
├── data/
│   ├── web_analytics.csv     # Demo web analytics (20 sessions, 5 campaigns)
│   ├── crm_data.csv          # Demo CRM data (20 rows, real rep-style notes)
│   └── fixture_results.json  # Cached GPT-4o output for DEMO_MODE
├── api/
│   ├── main.py               # FastAPI app — health + waitlist routes
│   ├── models.py             # Pydantic request/response models
│   ├── db.py                 # Postgres connection + DDL helpers
│   └── email_utils.py        # SMTP notification helper
├── landing/                  # Next.js 14 marketing / waitlist site
│   ├── app/                  # App Router pages and layout
│   ├── components/           # React components (Hero, Waitlist form, etc.)
│   ├── Dockerfile            # Node 20 Alpine multi-stage build
│   └── next.config.ts        # output: standalone for Docker
├── scripts/
│   └── generate_fixture.py   # Regenerate fixture from a live GPT-4o run
├── tests/
│   ├── test_llm.py           # LLM unit tests
│   ├── test_data.py          # Data layer tests
│   ├── test_api.py           # FastAPI route contract tests
│   ├── test_phase7_landing.py # Landing page component tests
│   └── test_deploy_config.py # Deploy config invariant tests
├── caddy/
│   └── Caddyfile             # Caddy reverse proxy — domain + routing rules
├── .streamlit/
│   └── config.toml           # Streamlit theme + CORS/XSRF settings
├── Dockerfile                # Multi-stage: builder → streamlit + api stages
├── compose.yaml              # Five-service stack: app, fastapi, landing, caddy, postgres
├── SECURITY.md               # Security policy and responsible disclosure
├── DEMO-SCRIPT.md            # Loom narration script
├── .env.example              # Environment variable template
├── pyproject.toml
└── uv.lock
```

---

## Use Cases

**Hackathon / demo** — Load demo data, click Run Analysis, show the table. Full flow in under 30 seconds with no API key via `DEMO_MODE=1`.

**Agency analyst** — Replace `data/web_analytics.csv` and `data/crm_data.csv` with a real client export, paste an API key, run analysis. Get a defensible budget recommendation backed by what the sales team actually said.

**Weekly budget review** — Export the previous week's analytics and CRM data, run the tool, use the action table as the agenda for the budget call.

**Sales + marketing alignment** — Show the stitched dataframe in a meeting. The `reasoning` column makes the AI decision transparent — it cites the actual sales-note language, not abstract scores.

---

## Limitations (MVP)

- UI reads from `data/` directory — no drag-and-drop file upload yet
- Designed for up to ~30 campaigns / ~200 sessions before context window quality degrades
- No multi-user auth — single-session Streamlit app
- No result persistence — analysis results live in `st.session_state` for the session only
