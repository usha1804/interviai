"""
ATS Resume Analyzer Service
Compares resume text against a job description using Groq AI.
Generates ATS score, keyword match %, missing skills, improvements, PDF report.
"""
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List
from xml.sax.saxutils import escape
from fastapi import HTTPException
from app.config import settings
from app.services.ai_service import _chat, get_groq_client

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
logger = logging.getLogger(__name__)

def _normalize_phrase(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+(?:[+#]+)?", value.casefold())
    return " ".join(tokens)


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {_normalize_phrase(text)} "
    normalized_phrase = _normalize_phrase(phrase)
    return bool(normalized_phrase) and f" {normalized_phrase} " in normalized_text


def _string_list(payload: dict, key: str, *, required: bool = True) -> List[str]:
    values = payload.get(key)
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        if required:
            raise ValueError(f"AI response field {key} must be a list of strings.")
        return []
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


def _percentage(payload: dict, key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100:
        raise ValueError(f"AI response field {key} must be a number from 0 to 100.")
    return float(value)


def analyze_ats(resume_text: str, jd_text: str) -> Dict:
    """Compare resume evidence with job requirements and return an estimated fit."""
    prompt = f"""You are an ATS evaluator. Use only evidence in the supplied job description and resume.
Do not invent candidate experience, qualifications, or skills. Return ONLY valid JSON.

Extract concise, distinct job keywords, required skills, preferred skills, and technical skills from
the job description. Assess experience, education, and project relevance by comparing the resume
with the job requirements. Give each assessment a 0-100 percentage. If a requirement is absent from
the resume, treat it as missing rather than assuming it is present.

JOB DESCRIPTION:
{jd_text[:6000]}

RESUME:
{resume_text[:8000]}

Return this JSON shape:
{{
  "job_keywords": ["terms explicitly relevant to this job"],
  "required_skills": ["skills explicitly required"],
  "preferred_skills": ["skills explicitly preferred"],
  "technical_skills": ["technical skills explicitly requested"],
  "experience_match_pct": 0,
  "education_match_pct": 0,
  "project_match_pct": 0,
  "strengths": ["evidence-based resume strengths"],
  "weaknesses": ["evidence-based gaps"],
  "improvements": ["specific, truthful resume improvements"],
  "formatting_suggestions": ["format suggestions only when relevant"],
  "ai_summary": "A concise evidence-based assessment."
}}"""

    text = _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=2200)
    try:
        start, end = text.find("{"), text.rfind("}") + 1
        if start < 0 or end <= start:
            raise ValueError("AI response did not contain a JSON object.")
        ai_result = json.loads(text[start:end])
        if not isinstance(ai_result, dict):
            raise ValueError("AI response was not a JSON object.")

        job_keywords = [
            item for item in _string_list(ai_result, "job_keywords")
            if _contains_phrase(jd_text, item)
        ]
        required_skills = [
            item for item in _string_list(ai_result, "required_skills")
            if _contains_phrase(jd_text, item)
        ]
        preferred_skills = [
            item for item in _string_list(ai_result, "preferred_skills")
            if _contains_phrase(jd_text, item)
        ]
        technical_skills = [
            item for item in _string_list(ai_result, "technical_skills")
            if _contains_phrase(jd_text, item)
        ]
        skills = list(dict.fromkeys(required_skills + preferred_skills + technical_skills))
        if not job_keywords or not skills:
            raise ValueError("AI response did not identify job keywords and skills from the description.")

        matched_keywords = [item for item in job_keywords if _contains_phrase(resume_text, item)]
        missing_keywords = [item for item in job_keywords if item not in matched_keywords]
        matching_skills = [item for item in skills if _contains_phrase(resume_text, item)]
        missing_skills = [item for item in skills if item not in matching_skills]
        missing_required_skills = [
            item for item in required_skills if not _contains_phrase(resume_text, item)
        ]
        missing_technologies = [
            item for item in technical_skills if not _contains_phrase(resume_text, item)
        ]

        keyword_match_pct = round(100 * len(matched_keywords) / len(job_keywords), 1)
        skills_match_pct = round(100 * len(matching_skills) / len(skills), 1)
        experience_match_pct = _percentage(ai_result, "experience_match_pct")
        education_match_pct = _percentage(ai_result, "education_match_pct")
        project_match_pct = _percentage(ai_result, "project_match_pct")
        ats_score = round(
            keyword_match_pct * 0.40
            + skills_match_pct * 0.30
            + experience_match_pct * 0.15
            + education_match_pct * 0.10
            + project_match_pct * 0.05
        )

        ai_summary = ai_result.get("ai_summary")
        if not isinstance(ai_summary, str) or not ai_summary.strip():
            raise ValueError("AI response is missing an evidence-based summary.")
        return {
            "ats_score": ats_score,
            "keyword_match_pct": keyword_match_pct,
            "skills_match_pct": skills_match_pct,
            "experience_match_pct": experience_match_pct,
            "education_match_pct": education_match_pct,
            "project_match_pct": project_match_pct,
            "job_keywords": job_keywords,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "required_skills": required_skills,
            "missing_required_skills": missing_required_skills,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "missing_technologies": missing_technologies,
            "recommended_keywords": list(dict.fromkeys(missing_required_skills + missing_keywords)),
            "strengths": _string_list(ai_result, "strengths"),
            "weaknesses": _string_list(ai_result, "weaknesses"),
            "improvements": _string_list(ai_result, "improvements"),
            "formatting_suggestions": _string_list(ai_result, "formatting_suggestions"),
            "ai_summary": ai_summary.strip(),
        }
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.exception("ATS analysis returned an invalid response")
        raise HTTPException(
            status_code=502,
            detail="ATS analysis could not be completed because the AI returned an invalid result. Please retry.",
        ) from exc


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
    story.append(Paragraph(
        f"Candidate: {escape(str(user_name))} | {datetime.utcnow().strftime('%Y-%m-%d')}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.4*cm))

    # Score table
    score_data = [
        ["Metric", "Score"],
        ["ATS Score", f"{report_data.get('ats_score', 0):.0f}/100"],
        ["Keyword Match", f"{report_data.get('keyword_match_pct', 0):.0f}%"],
        ["Skills Match", f"{report_data.get('skills_match_pct', 0):.0f}%"],
        ["Experience Match", f"{report_data.get('experience_match_pct', 0):.0f}%"],
        ["Education Match", f"{report_data.get('education_match_pct', 0):.0f}%"],
        ["Project Relevance", f"{report_data.get('project_match_pct', 0):.0f}%"],
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
    story.append(Paragraph(escape(report_data.get("ai_summary", "N/A")), styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    for label, key in [
        ("Matching Skills", "matching_skills"),
        ("Missing Skills", "missing_skills"),
        ("Recommended Keywords", "recommended_keywords"),
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
                story.append(Paragraph(f"• {escape(str(item))}", styles["Normal"]))
            story.append(Spacer(1, 0.2*cm))

    doc.build(story)
    return path
