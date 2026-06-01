from llm import AnalysisResult


def _badge_html(action: str) -> str:
    colors = {
        "increase": "background:#09ab3b; color:#ffffff;",
        "pause": "background:#ff2b2b; color:#ffffff;",
        "decrease": "background:#faca2b; color:#262730;",
        "insufficient_data": "background:#808495; color:#ffffff;",
    }
    labels = {
        "increase": "INCREASE",
        "pause": "PAUSE",
        "decrease": "DECREASE",
        "insufficient_data": "INSUFFICIENT DATA",
    }
    style = colors.get(action, "background:#808495; color:#ffffff;")
    label = labels.get(action, action.upper())
    return (
        f'<span style="display:inline-block; padding:4px 8px; border-radius:12px; '
        f'font-size:12px; font-weight:600; letter-spacing:0.5px; {style}">{label}</span>'
    )


def _pct_html(value: int) -> str:
    if value > 0:
        return f'<span style="color:#09ab3b; font-weight:600;">+{value}%</span>'
    elif value < 0:
        return f'<span style="color:#ff2b2b; font-weight:600;">{value}%</span>'
    else:
        return '<span style="color:#808495; font-weight:600;">0%</span>'


def build_results_table_html(result: AnalysisResult) -> str:
    rows = ""
    for c in result.campaigns:
        rows += (
            f"<tr style='border-bottom:1px solid #e6e9ef;'>"
            f"<td style='padding:8px 12px;'>{c.campaign_id}</td>"
            f"<td style='padding:8px 12px;'>{_badge_html(c.budget_action)}</td>"
            f"<td style='padding:8px 12px;'>{_pct_html(c.percentage_change)}</td>"
            f"<td style='padding:8px 12px;'>{c.semantic_reasoning}</td>"
            f"<td style='padding:8px 12px;'>{round(c.confidence * 100)}%</td>"
            f"<td style='padding:8px 12px;'>{c.evidence_count}</td>"
            f"</tr>"
        )
    return (
        "<table style='width:100%; border-collapse:collapse; "
        'font-family:"IBM Plex Mono", monospace; font-size:14px; margin:1.5rem 0;\'>'
        "<thead><tr style='background:#f0f2f6;'>"
        "<th style='padding:8px 12px; font-weight:600; color:#262730; border-bottom:2px solid #e6e9ef; text-align:left;'>campaign_id</th>"
        "<th style='padding:8px 12px; font-weight:600; color:#262730; border-bottom:2px solid #e6e9ef; text-align:left;'>action</th>"
        "<th style='padding:8px 12px; font-weight:600; color:#262730; border-bottom:2px solid #e6e9ef; text-align:left;'>budget_change_%</th>"
        "<th style='padding:8px 12px; font-weight:600; color:#262730; border-bottom:2px solid #e6e9ef; text-align:left;'>reasoning</th>"
        "<th style='padding:8px 12px; font-weight:600; color:#262730; border-bottom:2px solid #e6e9ef; text-align:left;'>confidence</th>"
        "<th style='padding:8px 12px; font-weight:600; color:#262730; border-bottom:2px solid #e6e9ef; text-align:left;'>sessions</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def build_exec_summary_html(summary: str) -> str:
    return (
        f"<div style='background:#f0f2f6; border-left:4px solid #f63366; "
        f"padding:1rem 1.5rem; margin-bottom:2rem; font-size:16px; "
        f'font-family:"IBM Plex Sans", sans-serif; color:#262730;\'>'
        f"<strong>This week:</strong> {summary}"
        f"</div>"
    )
