"""
ATS Resume Analyzer Service
Compares resume text against a job description using Groq AI.
Generates ATS score, keyword match %, missing skills, improvements, PDF report.
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, Optional
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def analyze_ats(resume_text: str, jd_text: str) -> Dict:
    """Run full ATS analysis — resume vs job description."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer and career coach.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{jd_text[:2000]}

Perform a comprehensive ATS analysis. Return ONLY valid JSON:
{{
    "ats_score": <0-100>,
    "keyword_match_pct": <0-100>,
    "matching_skills": ["<skill1>", "<skill2>"],
    "missing_skills": ["<skill1>", "<skill2>"],
    "missing_technologies": ["<tech1>", "<tech2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "weaknesses": ["<weakness1>", "<weakness2>"],
    "improvements": ["<improvement1>", "<improvement2>", "<improvement3>"],
    "formatting_suggestions": ["<suggestion1>", "<suggestion2>"],
    "ai_summary": "<3-4 sentence executive summary of resume fit for this role>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=2000)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {
            "ats_score": 50, "keyword_match_pct": 40,
            "matching_skills": [], "missing_skills": [],
            "missing_technologies": [], "strengths": [],
            "weaknesses": [], "improvements": [],
            "formatting_suggestions": [],
            "ai_summary": "Analysis unavailable. Please try again.",
        }


def generate_ats_pdf(report_data: Dict, user_name: str, report_id: int) -> str:
    """Generate a downloadable ATS report PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm

    filename = f"ats_report_{report_id}.pdf"
    path = os.path.join(REPORTS_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    accent = colors.HexColor("#6366f1")
    title_style = ParagraphStyle("t", parent=styles["Title"], textColor=accent, fontSize=20)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=accent)

    story.append(Paragraph("InterviAI — ATS Resume Analysis Report", title_style))
    story.append(Paragraph(f"Candidate: {user_name} | {datetime.utcnow().strftime('%Y-%m-%d')}", styles["Normal"]))
    story.append(Spacer(1, 0.4*cm))

    # Score table
    score_data = [
        ["Metric", "Score"],
        ["ATS Score", f"{report_data.get('ats_score', 0):.0f}/100"],
        ["Keyword Match", f"{report_data.get('keyword_match_pct', 0):.0f}%"],
        ["Matching Skills", str(len(report_data.get('matching_skills', [])))],
        ["Missing Skills", str(len(report_data.get('missing_skills', [])))],
    ]
    t = Table(score_data, colWidths=[9*cm, 7*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("AI Summary", h2))
    story.append(Paragraph(report_data.get("ai_summary", "N/A"), styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    for label, key in [
        ("Matching Skills", "matching_skills"),
        ("Missing Skills", "missing_skills"),
        ("Missing Technologies", "missing_technologies"),
        ("Strengths", "strengths"),
        ("Weaknesses", "weaknesses"),
        ("Improvements", "improvements"),
        ("Formatting Suggestions", "formatting_suggestions"),
    ]:
        items = report_data.get(key, [])
        if items:
            story.append(Paragraph(label, h2))
            for item in items:
                story.append(Paragraph(f"• {item}", styles["Normal"]))
            story.append(Spacer(1, 0.2*cm))

    doc.build(story)
    return path
