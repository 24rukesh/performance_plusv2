# Requirements — Performance Plus v3.0

**Milestone:** v3.0 Advanced Analytics & Multi-Source
**Status:** Active
**Last updated:** 2026-06-02

---

## v3.0 Requirements

### Multi-Source Ingestion (INGEST)

- [ ] **INGEST-01**: User can upload multiple ad platform CSVs (Google Ads, Meta Ads, LinkedIn, or custom), assigning a platform name and currency to each upload before running analysis
- [ ] **INGEST-02**: User can map their CRM CSV's columns to standard fields (session_id, lead_status, projected_value, sales_notes) using an auto-suggest UI that proposes matches and requires explicit confirmation before the merge proceeds
- [x] **INGEST-03**: System normalizes all ad platform cost columns to USD using a static FX_RATES dictionary before any aggregation, so cross-platform spend totals are financially meaningful

### Richer Agent Logic (AGENT)

- [x] **AGENT-01**: User receives AI budget recommendations that reference cross-platform comparisons (e.g., which platform delivers better lead quality per dollar spent), based on the unified multi-source dataset
- [x] **AGENT-02**: Each campaign action in the results includes a `source_platforms` list identifying which ad platforms contributed sessions to that campaign
- [x] **AGENT-03**: System token-counts the aggregated payload with tiktoken before every gpt-4o call and warns the user if the payload approaches 60k tokens, preventing context window overflow

### Dynamic Views (VIEW)

- [x] **VIEW-01**: User can view a spend vs qualified leads scatter chart (color-coded by platform) and an action distribution chart for the current analysis, presented in a tabbed layout alongside the data preview and AI recommendations
- [ ] **VIEW-02**: User can filter results by platform, action type, and campaign name, and sort results by spend, campaign name, or recommended action
- [ ] **VIEW-03**: User can select up to 3 campaigns for side-by-side comparison and drill down to session-level rows for any campaign in the results view

### Analysis Management (MGMT)

- [ ] **MGMT-01**: User can save the current analysis to Postgres with a label, and reload any past saved analysis from a sidebar list without re-uploading CSV files
- [ ] **MGMT-02**: User can download the current analysis as a PDF report (via fpdf2) and as a CSV file, both via st.download_button
- [ ] **MGMT-03**: When the OpenAI API is unavailable, the app falls back to a cached fixture response (DEMO_MODE) so the demo remains functional offline

---

## Future Requirements (deferred from v3.0)

- Live exchange rate API integration (static FX_RATES sufficient for v3.0)
- Real Meta/Google/LinkedIn OAuth API connectors (CSV-first until multi-source value is proven)
- More than 5 simultaneous platform uploads (context window degrades beyond this)
- Branded PDF templates and scheduled/recurring analysis
- Shared team workspaces and multi-tenant isolation

---

## Out of Scope

- OAuth / direct API integrations with ad platforms — CSV-first this milestone; full API wiring is v4+
- Real user auth / login / accounts — waitlist-only; auth adds 2–3 phases
- Stripe / billing — no paid tier yet
- Redis job queue / async background jobs — synchronous calls sufficient at current scale
- HubSpot / Salesforce direct API pull — generic CSV covers current needs

---

## Traceability

| REQ-ID | Phase | Plan |
|--------|-------|------|
| INGEST-01 | Phase 9 | — |
| INGEST-02 | Phase 9 | — |
| INGEST-03 | Phase 9 | 09-01 ✅ |
| AGENT-01 | Phase 10 | — |
| AGENT-02 | Phase 10 | — |
| AGENT-03 | Phase 10 | — |
| VIEW-01 | Phase 11 | 11-02 ✅ |
| VIEW-02 | Phase 11 | — |
| VIEW-03 | Phase 11 | — |
| MGMT-01 | Phase 12 | — |
| MGMT-02 | Phase 11 | — |
| MGMT-03 | Phase 12 | — |
