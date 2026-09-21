"""PDF report generation (ReportLab) for the final interview report."""
from __future__ import annotations

import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

styles = getSampleStyleSheet()
_h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceAfter=8)
_h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
_body = styles["BodyText"]


def _bullets(items: List[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, _body)) for item in items] or [ListItem(Paragraph("None", _body))],
        bulletType="bullet",
    )


def generate_report_pdf(report: Dict[str, Any]) -> bytes:
    """Build the downloadable interview report PDF.

    `report` is expected to contain the keys produced by ReportService.build_report_payload().
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    story.append(Paragraph("AI Mock Interview — Final Report", _h1))
    story.append(Paragraph(f"Candidate: {report.get('candidate_name', 'N/A')}", _body))
    story.append(Paragraph(f"Category: {report.get('category', 'N/A')} | Target Company: {report.get('target_company', 'N/A')}", _body))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Executive Summary", _h2))
    story.append(Paragraph(report.get("executive_summary", ""), _body))

    story.append(Paragraph("2. Overall Score", _h2))
    story.append(Paragraph(f"Final Rating: <b>{report.get('final_rating')}</b> — Grade: <b>{report.get('grade')}</b>", _body))

    story.append(Paragraph("3. Skill-wise Score Card", _h2))
    skill_rows = [["Skill", "Average Score"]] + [
        [s.get("skill"), str(s.get("average_score"))] for s in report.get("skill_scorecard", [])
    ]
    table = Table(skill_rows, colWidths=[10 * cm, 5 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(table)

    story.append(Paragraph("4. Communication Assessment", _h2))
    story.append(Paragraph(report.get("communication_assessment", ""), _body))

    story.append(Paragraph("5. Technical Assessment", _h2))
    story.append(Paragraph(report.get("technical_assessment", ""), _body))

    story.append(Paragraph("6. Behavioral Assessment", _h2))
    story.append(Paragraph(report.get("behavioral_assessment", ""), _body))

    story.append(Paragraph("7. Areas of Improvement", _h2))
    story.append(_bullets(report.get("areas_of_improvement", [])))

    story.append(Paragraph("8. Recommended Learning Path", _h2))
    story.append(_bullets(report.get("learning_path", [])))

    story.append(Paragraph("9. Sample Ideal Answers", _h2))
    for item in report.get("sample_ideal_answers", []):
        story.append(Paragraph(f"<b>Q:</b> {item.get('question', '')}", _body))
        story.append(Paragraph(f"<b>Ideal Answer:</b> {item.get('ideal_answer', '')}", _body))
        story.append(Spacer(1, 6))

    story.append(Paragraph("10. Hiring Recommendation", _h2))
    story.append(Paragraph(report.get("hiring_recommendation", ""), _body))

    doc.build(story)
    return buffer.getvalue()
