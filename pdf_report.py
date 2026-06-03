from __future__ import annotations

import datetime  # noqa: F401  # reserved for future date formatting helpers
from typing import TYPE_CHECKING

from fpdf import FPDF

if TYPE_CHECKING:
    from llm import AnalysisResult


def generate_pdf(result: "AnalysisResult", meta: dict) -> bytes:
    """Generate a PDF report and return it as bytes for st.download_button.

    Args:
        result: Validated AnalysisResult from the LLM (read-only).
        meta: dict with keys: date, platforms_used, session_count, reporting_currency.

    Returns:
        PDF as bytes (bytearray wrapped in bytes() — required by st.download_button).
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- Header block ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Performance Plus", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0,
        6,
        (
            f"Date: {meta['date']}  |  Platforms: {meta['platforms_used']}"
            f"  |  Sessions: {meta['session_count']}  |  Currency: {meta['reporting_currency']}"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    # --- Executive summary ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, result.executive_summary)
    pdf.ln(6)

    # --- Campaign table ---
    # D-08: columns — Campaign ID | Action | Change (%) | Confidence | Sessions | Platforms
    table_data = [["Campaign ID", "Action", "Change (%)", "Confidence", "Sessions", "Platforms"]]
    for c in result.campaigns:
        table_data.append(
            [
                c.campaign_id,
                c.budget_action.upper(),
                f"{c.percentage_change:+d}%",
                f"{round(c.confidence * 100)}%",
                str(c.evidence_count),
                ", ".join(c.source_platforms) if c.source_platforms else "—",
            ]
        )

    pdf.set_font("Helvetica", "", 10)
    with pdf.table(
        borders_layout="MINIMAL",
        cell_fill_mode="ROWS",
        line_height=pdf.font_size * 2.5,
    ) as table:
        for row_data in table_data:
            row = table.row()
            for cell in row_data:
                row.cell(cell)

    return bytes(pdf.output())  # bytearray -> bytes; required by st.download_button
