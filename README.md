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

### Docker (self-hosted VPS)

```bash
# 1. Create .env on the server (never commit this)
cp .env.example .env
# Edit .env: set DEMO_MODE=1 (and optionally OPENAI_API_KEY)

# 2. Build and start
docker compose up -d --build

# 3. Check services
docker compose ps
docker compose logs caddy --tail=50   # confirm Let's Encrypt cert
```

Edit `caddy/Caddyfile` to replace `agent.rukesh.in` with your domain before deploying.

### Coolify

1. Add New Resource → Application → connect your Git repo
2. Build pack: **Dockerfile**, Port: **8501**
3. Set environment variables: `DEMO_MODE=1` (and `OPENAI_API_KEY` if you want server-side live mode)
4. Set your domain, enable HTTPS
5. Deploy

> Do not set `OPENAI_API_KEY` on the server if you want the public-facing demo mode UI to show. The `DEMO_MODE` badge only renders when no server-side key is present — judges and visitors use their own key via the sidebar if they want a live call.

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
├── app.py                  # Streamlit UI — main entry point
├── llm.py                  # GPT-4o client, Pydantic schema, run_analysis()
├── data.py                 # CSV ingestion and session_id merge
├── ui_helpers.py           # HTML table and badge rendering
├── data_generator.py       # Synthetic demo data generator
├── data/
│   ├── web_analytics.csv   # Demo web analytics (20 sessions, 5 campaigns)
│   ├── crm_data.csv        # Demo CRM data (20 rows, real rep-style notes)
│   └── fixture_results.json  # Cached GPT-4o output for DEMO_MODE
├── scripts/
│   └── generate_fixture.py # Regenerate fixture from a live GPT-4o run
├── tests/
│   ├── test_llm.py         # LLM unit tests (10 tests)
│   ├── test_data.py        # Data layer tests
│   └── test_deploy_config.py  # Deploy config invariant tests (8 tests)
├── caddy/
│   └── Caddyfile           # Caddy reverse proxy config
├── .streamlit/
│   └── config.toml         # Theme + CORS/XSRF settings
├── Dockerfile              # Multi-stage build
├── compose.yaml            # App + Caddy services
├── DEMO-SCRIPT.md          # Loom narration script
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
