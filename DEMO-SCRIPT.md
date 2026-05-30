# Performance Plus — Loom Demo Script (2-3 min)

**Audience:** Hackathon judges (OpenAI x Outskill AI Builders Cohort 01)
**Live URL:** https://agent.rukesh.in

---

## Section 1: Problem & Hook

**Time:** 0:00 – 0:30

**Say:**
> "Every performance marketer has the same blind spot. You've got a dashboard full of click data — impressions, cost-per-click, conversion rates — but none of that tells you what your sales reps actually said about the leads those campaigns generated. A campaign can look great on paper and be full of completely wrong-ICP leads. Right now, budget routing is blind to that qualitative signal. Performance Plus fixes that."

**Show on screen:**
- Open https://agent.rukesh.in in a fresh browser window
- Point at the page loading cleanly over HTTPS

---

## Section 2: Full Click-Through Flow

**Time:** 0:30 – 1:45

**Say:**
> "Let me show you the full flow. I'll open the app — you can see the blue banner at the top telling us we're in demo mode, running from cached results. The sidebar shows the green Demo Mode badge instead of an API key prompt. Now I'll click Load Demo Data."

**Show on screen:**
- Point at the blue info banner: "ℹ️ Running in demo mode — cached results, no live API call"
- Point at the sidebar green badge: "✅ Demo Mode — running with cached results"
- Click **Load demo data**

**Say:**
> "What you're looking at now is the stitched dataframe — 20 sessions, joined on session_id. Every row has both the web analytics columns — clicks, impressions, cost, conversion rate — and the CRM columns — lead status, projected value, and the actual sales rep notes. That join is the core of the attribution layer. Now let me click Run Analysis."

**Show on screen:**
- Point at the Stitched Dataframe Preview with 20 rows
- Point at a row and gesture at both web analytics and CRM columns side-by-side
- Click **Run Analysis**

**Say:**
> "The model comes back with an executive summary and a campaign-by-campaign action table. Let me read you the summary — [read executive_summary line aloud]. Now look at the individual decisions. Take cmp_competitor_conquest — it gets an INCREASE. And look at the reasoning: it's citing actual language from the sales notes. Now look at cmp_b2b_search — that's a PAUSE with minus 100 percent, because the reps flagged wrong ICP across all sessions. That's a qualitative signal overriding what the click data alone would have said."

**Show on screen:**
- Point at the executive summary card
- Point at `cmp_competitor_conquest` row — INCREASE badge, read semantic_reasoning aloud
- Point at `cmp_b2b_search` row — PAUSE badge, read semantic_reasoning aloud
- Gesture at the full 5-campaign color-coded table

---

## Section 3: DEMO_MODE Callout

**Time:** 1:45 – 2:15

**Say:**
> "Now — I want to be transparent about what you just saw. The public URL runs with DEMO_MODE=1 set on the server, which means the results came from a pre-cached fixture rather than a live gpt-4o call right now. But here's what matters: this fixture was generated from a real gpt-4o run against this exact dataset. The AI reasoning is real — these are the actual budget decisions gpt-4o made when it read these sales notes. Nothing is faked, only cached — so that the demo works reliably even if the OpenAI API has latency on the day you watch this. A judge who pastes their own API key in the sidebar gets a live call instead."

**Show on screen:**
- Point at the blue banner again
- Optionally show the sidebar — note that pasting a real key would switch to live mode

---

## Section 4: Technical Stack Callout

**Time:** 2:15 – 3:00

**Say:**
> "Under the hood — the AI layer uses gpt-4o Structured Outputs via `client.beta.chat.completions.parse()`, with the model pinned to `gpt-4o-2024-08-06`, the earliest snapshot that supports Structured Outputs. The response schema is enforced by Pydantic v2 schema enforcement — so the model cannot return a malformed action type or an out-of-range confidence score. That's what makes the output deterministic enough to route budget decisions programmatically. The data layer is a Pandas inner join with `validate='m:1'` on session_id — that one line is what guarantees we never send a row with missing CRM context to the model. The whole thing runs in a Streamlit app, containerised with Docker, deployed on a self-hosted VPS."

**Show on screen:**
- Return to the results table — gesture at it as you name the stack
- The visual evidence of working structured output is the table itself

---

**Target total runtime: 2:00 – 3:00.**
