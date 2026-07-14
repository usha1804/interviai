"""
Report service — generates enhanced interview reports with PDF export.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    InterviewSession, Question, Answer,
    EnhancedInterviewReport, CodingSession, ProctoringSession,
)
from app.services.multi_agent_service import coordinator
from app.services.rag_service import retrieve_resume_context, retrieve_jd_context

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_enhanced_report(session_id: int, user_id: int, db: Session) -> EnhancedInterviewReport:
    """Build full report using PerformanceAgent + optional coding/proctoring data."""

    # Check for existing report
    existing = db.query(EnhancedInterviewReport).filter(
        EnhancedInterviewReport.session_id == session_id
    ).first()
    if existing:
        return existing

    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    answers = db.query(Answer).join(Question).filter(Question.session_id == session_id).all()

    answers_data = []
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        answers_data.append({
            "question": q.question_text if q else "",
            "answer": a.user_answer,
            "score": a.score or 0,
        })

    resume_ctx = retrieve_resume_context(user_id, "skills experience")
    jd_ctx = retrieve_jd_context(user_id, "required skills")

    analysis = coordinator.analyze_full_interview(
        answers_data=answers_data,
        interview_type=session.interview_type if session else "TECHNICAL",
        resume_ctx=resume_ctx,
        jd_ctx=jd_ctx,
    )

    # Pull coding score if available
    coding_session = db.query(CodingSession).filter(
        CodingSession.user_id == user_id
    ).order_by(CodingSession.created_at.desc()).first()
    coding_score = coding_session.score if coding_session else None

    # Pull proctoring confidence
    proc = db.query(ProctoringSession).filter(
        ProctoringSession.session_key == f"interview_{session_id}"
    ).first()
    confidence_score = proc.confidence_score if proc else analysis.get("confidence_score", 60)

    report = EnhancedInterviewReport(
        session_id=session_id,
        user_id=user_id,
        technical_score=analysis.get("technical_score"),
        communication_score=analysis.get("communication_score"),
        coding_score=coding_score,
        confidence_score=confidence_score,
        overall_score=analysis.get("overall_score"),
        hiring_probability=analysis.get("hiring_probability"),
        skill_matrix=analysis.get("skill_matrix", {}),
        radar_chart_data=analysis.get("radar_chart_data", []),
        strengths=analysis.get("strengths", []),
        weaknesses=analysis.get("weaknesses", []),
        topics_to_improve=analysis.get("topics_to_improve", []),
        learning_recommendations=analysis.get("learning_recommendations", []),
        ai_summary=analysis.get("ai_summary"),
        hiring_recommendation=analysis.get("hiring_recommendation", "MAYBE"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Generate PDF
    try:
        pdf_path = _generate_pdf(report, answers_data)
        report.pdf_path = pdf_path
        db.commit()
    except Exception:
        pass

    return report


def _generate_pdf(report: EnhancedInterviewReport, answers_data: List[Dict]) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm

    filename = f"report_{report.session_id}_{report.user_id}.pdf"
    path = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("title", parent=styles["Title"], textColor=colors.HexColor("#6366f1"))
    story.append(Paragraph("InterviAI — Interview Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # Scores table
    score_data = [
        ["Metric", "Score"],
        ["Overall Score", f"{report.overall_score or 0:.1f}/100"],
        ["Technical Score", f"{report.technical_score or 0:.1f}/100"],
        ["Communication Score", f"{report.communication_score or 0:.1f}/100"],
        ["Confidence Score", f"{report.confidence_score or 0:.1f}/100"],
        ["Hiring Probability", f"{report.hiring_probability or 0:.1f}%"],
        ["Recommendation", report.hiring_recommendation or "N/A"],
    ]
    t = Table(score_data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # AI Summary
    story.append(Paragraph("AI Summary", styles["Heading2"]))
    story.append(Paragraph(report.ai_summary or "N/A", styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    # Strengths & Weaknesses
    for label, items in [("Strengths", report.strengths), ("Areas to Improve", report.weaknesses)]:
        story.append(Paragraph(label, styles["Heading3"]))
        for item in (items or []):
            story.append(Paragraph(f"• {item}", styles["Normal"]))
        story.append(Spacer(1, 0.2*cm))

    # Topics to improve
    if report.topics_to_improve:
        story.append(Paragraph("Topics to Study", styles["Heading3"]))
        for t in report.topics_to_improve:
            story.append(Paragraph(f"• {t}", styles["Normal"]))

    doc.build(story)
    return path
