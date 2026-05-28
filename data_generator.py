import pathlib
import pandas as pd

_HERE = pathlib.Path(__file__).parent

_WEB_ANALYTICS_ROWS = [
    {"session_id": "sess_001", "campaign_id": "cmp_b2b_search",         "clicks": 142, "impressions": 4800,  "cost_usd": 87.50,  "conversion_rate": 0.031},
    {"session_id": "sess_002", "campaign_id": "cmp_competitor_conquest", "clicks": 38,  "impressions": 2100,  "cost_usd": 42.00,  "conversion_rate": 0.078},
    {"session_id": "sess_003", "campaign_id": "cmp_b2b_search",         "clicks": 118, "impressions": 5100,  "cost_usd": 92.00,  "conversion_rate": 0.028},
    {"session_id": "sess_004", "campaign_id": "cmp_competitor_conquest", "clicks": 44,  "impressions": 1900,  "cost_usd": 38.50,  "conversion_rate": 0.084},
    {"session_id": "sess_005", "campaign_id": "cmp_b2b_search",         "clicks": 156, "impressions": 5300,  "cost_usd": 101.00, "conversion_rate": 0.033},
    {"session_id": "sess_006", "campaign_id": "cmp_competitor_conquest", "clicks": 52,  "impressions": 2400,  "cost_usd": 48.00,  "conversion_rate": 0.091},
    {"session_id": "sess_007", "campaign_id": "cmp_b2b_search",         "clicks": 131, "impressions": 4600,  "cost_usd": 84.00,  "conversion_rate": 0.029},
    {"session_id": "sess_008", "campaign_id": "cmp_competitor_conquest", "clicks": 29,  "impressions": 1700,  "cost_usd": 35.00,  "conversion_rate": 0.071},
    {"session_id": "sess_009", "campaign_id": "cmp_b2b_search",         "clicks": 109, "impressions": 4200,  "cost_usd": 77.50,  "conversion_rate": 0.026},
    {"session_id": "sess_010", "campaign_id": "cmp_retargeting",        "clicks": 87,  "impressions": 3200,  "cost_usd": 65.00,  "conversion_rate": 0.042},
    {"session_id": "sess_011", "campaign_id": "cmp_retargeting",        "clicks": 74,  "impressions": 2900,  "cost_usd": 58.00,  "conversion_rate": 0.038},
    {"session_id": "sess_012", "campaign_id": "cmp_retargeting",        "clicks": 93,  "impressions": 3400,  "cost_usd": 71.00,  "conversion_rate": 0.049},
    {"session_id": "sess_013", "campaign_id": "cmp_retargeting",        "clicks": 61,  "impressions": 2700,  "cost_usd": 53.50,  "conversion_rate": 0.035},
    {"session_id": "sess_014", "campaign_id": "cmp_linkedin_outbound",  "clicks": 45,  "impressions": 3800,  "cost_usd": 95.00,  "conversion_rate": 0.018},
    {"session_id": "sess_015", "campaign_id": "cmp_linkedin_outbound",  "clicks": 38,  "impressions": 3500,  "cost_usd": 88.00,  "conversion_rate": 0.015},
    {"session_id": "sess_016", "campaign_id": "cmp_linkedin_outbound",  "clicks": 51,  "impressions": 4100,  "cost_usd": 102.00, "conversion_rate": 0.021},
    {"session_id": "sess_017", "campaign_id": "cmp_brand_awareness",    "clicks": 210, "impressions": 7800,  "cost_usd": 145.00, "conversion_rate": 0.008},
    {"session_id": "sess_018", "campaign_id": "cmp_brand_awareness",    "clicks": 187, "impressions": 7100,  "cost_usd": 132.00, "conversion_rate": 0.009},
    {"session_id": "sess_019", "campaign_id": "cmp_b2b_search",         "clicks": 124, "impressions": 4900,  "cost_usd": 89.00,  "conversion_rate": 0.030},
    {"session_id": "sess_020", "campaign_id": "cmp_competitor_conquest", "clicks": 41,  "impressions": 1950,  "cost_usd": 40.00,  "conversion_rate": 0.076},
]

_CRM_ROWS = [
    {"session_id": "sess_001", "campaign_id": "cmp_b2b_search",         "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Lead thought we were a consumer app. Angry when I mentioned enterprise pricing. Bad targeting."},
    {"session_id": "sess_002", "campaign_id": "cmp_competitor_conquest", "lead_status": "Qualified",    "projected_value": 5000.00, "sales_notes": "Perfect fit. Loved the ROI dashboard feature. Ready to sign next week."},
    {"session_id": "sess_003", "campaign_id": "cmp_b2b_search",         "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Wrong segment, looking for SMB tooling, not enterprise. Not worth following up."},
    {"session_id": "sess_004", "campaign_id": "cmp_competitor_conquest", "lead_status": "Qualified",    "projected_value": 8500.00, "sales_notes": "Came from competitor X, ready to switch. Pricing aligned, contract review in progress."},
    {"session_id": "sess_005", "campaign_id": "cmp_b2b_search",         "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Asked about consumer features, not enterprise. Confused about our product category."},
    {"session_id": "sess_006", "campaign_id": "cmp_competitor_conquest", "lead_status": "Qualified",    "projected_value": 6200.00, "sales_notes": "Decision-maker on call, strong interest in attribution features. Deciding next month."},
    {"session_id": "sess_007", "campaign_id": "cmp_b2b_search",         "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Budget too small, decision-maker not involved. Misaligned from the start."},
    {"session_id": "sess_008", "campaign_id": "cmp_competitor_conquest", "lead_status": "Qualified",    "projected_value": 4800.00, "sales_notes": "Previously using a legacy tool, impressed by our CRM integration demo. High buy intent."},
    {"session_id": "sess_009", "campaign_id": "cmp_b2b_search",         "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Looking for a free tool, pushed back on pricing immediately. Not enterprise-grade buyer."},
    {"session_id": "sess_010", "campaign_id": "cmp_retargeting",        "lead_status": "Nurture",      "projected_value": 1200.00, "sales_notes": "Still evaluating, revisited pricing page twice. Needs more time before committing."},
    {"session_id": "sess_011", "campaign_id": "cmp_retargeting",        "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Revisited the site but ultimately went with a cheaper option. Not a fit at this price."},
    {"session_id": "sess_012", "campaign_id": "cmp_retargeting",        "lead_status": "Nurture",      "projected_value": 2100.00, "sales_notes": "Warm lead, opened 3 follow-up emails. Scheduled a second demo call for next week."},
    {"session_id": "sess_013", "campaign_id": "cmp_retargeting",        "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Re-engaged briefly but team budget frozen until Q3. Unlikely to close this quarter."},
    {"session_id": "sess_014", "campaign_id": "cmp_linkedin_outbound",  "lead_status": "Nurture",      "projected_value": 800.00,  "sales_notes": "Connected on LinkedIn, lukewarm interest. Has not responded to last two follow-ups."},
    {"session_id": "sess_015", "campaign_id": "cmp_linkedin_outbound",  "lead_status": "Nurture",      "projected_value": 600.00,  "sales_notes": "Slow follow-up, initially interested but now unresponsive. May need a break in cadence."},
    {"session_id": "sess_016", "campaign_id": "cmp_linkedin_outbound",  "lead_status": "Nurture",      "projected_value": 950.00,  "sales_notes": "Soft interest only, no clear use case articulated. Will revisit in 60 days."},
    {"session_id": "sess_017", "campaign_id": "cmp_brand_awareness",    "lead_status": "Nurture",      "projected_value": 300.00,  "sales_notes": "Top-of-funnel only, no specific pain point surfaced yet. Early awareness stage."},
    {"session_id": "sess_018", "campaign_id": "cmp_brand_awareness",    "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "Clicked through from a broad awareness ad, not a decision-maker, no follow-up needed."},
    {"session_id": "sess_019", "campaign_id": "cmp_b2b_search",         "lead_status": "Disqualified", "projected_value": 0.00,    "sales_notes": "No enterprise need, mentioned they run a small agency. Completely out of our ICP."},
    {"session_id": "sess_020", "campaign_id": "cmp_competitor_conquest", "lead_status": "Qualified",    "projected_value": 5500.00, "sales_notes": "Strong referral from an existing customer. Motivated to switch before Q3 budget cycle."},
]


def generate_web_analytics() -> pd.DataFrame:
    return pd.DataFrame(_WEB_ANALYTICS_ROWS)


def generate_crm_data() -> pd.DataFrame:
    return pd.DataFrame(_CRM_ROWS)


def write_csvs(output_dir: pathlib.Path | None = None) -> None:
    if output_dir is None:
        output_dir = _HERE / "data"
    output_dir.mkdir(exist_ok=True)
    generate_web_analytics().to_csv(output_dir / "web_analytics.csv", index=False)
    generate_crm_data().to_csv(output_dir / "crm_data.csv", index=False)
    print(f"Wrote CSVs to {output_dir}/")


if __name__ == "__main__":
    write_csvs()
