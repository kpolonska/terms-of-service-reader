import io
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from services.scoring_service import compute_score

_project_root = Path(__file__).resolve().parent.parent.parent
_DB_PATH = os.environ.get("DATABASE_PATH", str(_project_root / "ai_pipeline" / "analyses.db"))

SEVERITY_COLORS = {
    "high":   colors.HexColor("#fee2e2"),
    "medium": colors.HexColor("#fef3c7"),
    "low":    colors.HexColor("#d1fae5"),
}

RISK_COLORS = {
    "SAFE":      colors.HexColor("#065f46"),
    "CAUTION":   colors.HexColor("#92400e"),
    "RISKY":     colors.HexColor("#9a3412"),
    "DANGEROUS": colors.HexColor("#991b1b"),
}


def get_latest_analysis(domain: str) -> dict | None:
    if not os.path.exists(_DB_PATH):
        return None
    with sqlite3.connect(_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT result_json, analyzed_at FROM analyses WHERE domain = ? ORDER BY analyzed_at DESC LIMIT 1",
            (domain,),
        ).fetchone()
    if not row:
        return None
    return {"result": json.loads(row["result_json"]), "analyzed_at": row["analyzed_at"]}


def generate_pdf(domain: str) -> bytes:
    record = get_latest_analysis(domain)
    if not record:
        raise ValueError(f"No analysis found for domain: {domain}")

    result = record["result"]
    analyzed_at = record["analyzed_at"]
    clauses = result.get("clauses", [])
    risk = compute_score(clauses)
    risk_label_display = result.get("risk_labels", {}).get(risk["label"].lower(), risk["label"])

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold", spaceAfter=4)
    sub_style = ParagraphStyle("sub", fontSize=10, textColor=colors.HexColor("#888888"), spaceAfter=12)
    section_style = ParagraphStyle("section", fontSize=12, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("body", fontSize=10, leading=15, spaceAfter=10)
    small_style = ParagraphStyle("small", fontSize=8, textColor=colors.HexColor("#888888"))

    risk_color = RISK_COLORS.get(risk["label"], colors.black)

    story = [
        Paragraph("ToS Reader", ParagraphStyle("logo", fontSize=11, textColor=colors.HexColor("#1e2952"), fontName="Helvetica-Bold")),
        Spacer(1, 4 * mm),
        Paragraph(f"Terms of Service Analysis — {domain}", title_style),
        Paragraph(f"Analyzed: {analyzed_at[:19].replace('T', ' ')} UTC", sub_style),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e5e5"), spaceAfter=10),

        # Risk score
        Table(
            [[
                Paragraph(f"{risk['score']}/10", ParagraphStyle("rscore", fontSize=22, fontName="Helvetica-Bold", textColor=risk_color)),
                Paragraph(
                    f"<b>{risk_label_display}</b><br/><font size=8 color='#888888'>Risk Score</font>",
                    ParagraphStyle("rlabel", fontSize=13, textColor=risk_color, leading=18),
                ),
            ]],
            colWidths=[25 * mm, 140 * mm],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
                ("ROUNDEDCORNERS", [4]),
            ]),
        ),
        Spacer(1, 6 * mm),

        # TLDR
        Paragraph("Summary", section_style),
        Paragraph(result.get("tldr", ""), body_style),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e5e5"), spaceAfter=6),

        # Clauses table
        Paragraph("Key Clauses", section_style),
    ]

    # Build clauses table
    header_style = ParagraphStyle("th", fontSize=9, fontName="Helvetica-Bold")
    cell_style = ParagraphStyle("td", fontSize=8, leading=12)

    table_data = [[
        Paragraph("Quote", header_style),
        Paragraph("Plain English", header_style),
        Paragraph("Category", header_style),
        Paragraph("Severity", header_style),
        Paragraph("Concept", header_style),
    ]]

    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5e5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]

    for i, clause in enumerate(clauses, start=1):
        sev = clause.get("severity", "low")
        category_label = clause.get("category_label") or clause.get("category", "").replace("_", " ")
        severity_label = clause.get("severity_label") or sev.upper()
        table_data.append([
            Paragraph(f'"{clause.get("quote", "")}"', cell_style),
            Paragraph(clause.get("plain_english", ""), cell_style),
            Paragraph(category_label, cell_style),
            Paragraph(severity_label, cell_style),
            Paragraph(clause.get("concept", ""), cell_style),
        ])
        bg = SEVERITY_COLORS.get(sev)
        if bg:
            row_styles.append(("BACKGROUND", (3, i), (3, i), bg))

    col_widths = [42 * mm, 52 * mm, 28 * mm, 18 * mm, 30 * mm]
    story.append(Table(table_data, colWidths=col_widths, style=TableStyle(row_styles), repeatRows=1))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e5e5")))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Generated by ToS Reader · For informational purposes only, not legal advice.", small_style))

    doc.build(story)
    return buf.getvalue()
