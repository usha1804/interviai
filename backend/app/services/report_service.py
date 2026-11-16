"""
Report service — generates enhanced interview reports with PDF export.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.config import settings
from app.models.models import (
    InterviewSession, Question, Answer,
    EnhancedInterviewReport,
)
from app.services.multi_agent_service import coordinator
from app.services.report_prompt_utils import (
    REPORT_MAX_ANSWER_CHARS,
    REPORT_MAX_BATCH_ANSWERS,
    REPORT_MAX_CONTEXT_CHARS,
    prompt_within_limits,
    select_relevant_context,
    split_text_preserving_content,
)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
logger = logging.getLogger(__name__)


def generate_enhanced_report(session_id: int, user_id: int, db: Session) -> EnhancedInterviewReport:
    """Build full report using PerformanceAgent + optional coding/proctoring data."""
    try:
        existing = db.query(EnhancedInterviewReport).filter(
            EnhancedInterviewReport.session_id == session_id,
            EnhancedInterviewReport.user_id == user_id,
        ).first()
        if existing:
            return existing

        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        interview_type = session.interview_type
        answers = (
            db.query(Answer)
            .join(Question)
            .options(joinedload(Answer.question))
            .filter(Question.session_id == session_id)
            .order_by(Question.id, Answer.id)
            .all()
        )
        answers_data = _compact_answer_records(answers)
        db.rollback()

        if not answers_data:
            analysis = {
                "technical_score": None,
                "communication_score": None,
                "overall_score": None,
                "hiring_probability": None,
                "hiring_recommendation": "NOT_EVALUATED",
                "skill_matrix": {},
                "radar_chart_data": [],
                "strengths": [],
                "weaknesses": [],
                "topics_to_improve": [],
                "learning_recommendations": [],
                "ai_summary": "No answers were evaluated. No performance score is available for this interview.",
            }
        else:
            resume_ctx = select_relevant_context(
                retrieve_report_resume_context(user_id, "skills experience projects"),
                "skills experience projects",
                REPORT_MAX_CONTEXT_CHARS,
            )
            jd_ctx = select_relevant_context(
                retrieve_report_jd_context(user_id, "required skills responsibilities"),
                "required skills responsibilities",
                REPORT_MAX_CONTEXT_CHARS,
            )
            analysis = _analyze_in_batches(
                answers_data,
                interview_type,
                resume_ctx,
                jd_ctx,
            )

        report = EnhancedInterviewReport(
            session_id=session_id,
            user_id=user_id,
            technical_score=analysis.get("technical_score"),
            communication_score=analysis.get("communication_score"),
            coding_score=None,
            confidence_score=None,
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

        try:
            pdf_path = _generate_pdf(report, answers_data)
            report.pdf_path = pdf_path
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Optional PDF generation failed for report session_id=%s", session_id)
        return report
    except Exception:
        db.rollback()
        raise


def retrieve_report_resume_context(user_id: int, query: str) -> str:
    from app.services.rag_service import retrieve_resume_context
    return retrieve_resume_context(user_id, query, k=4)


def retrieve_report_jd_context(user_id: int, query: str) -> str:
    from app.services.rag_service import retrieve_jd_context
    return retrieve_jd_context(user_id, query, k=4)


def _compact_answer_records(answers: List[Answer]) -> List[Dict]:
    """Keep distinct Q/A content and numeric evaluation evidence, not duplicate text."""
    records = {}
    for answer in answers:
        question = answer.question
        if question is None:
            continue
        question_text = question.question_text or ""
        answer_text = answer.user_answer or ""
        key = (
            " ".join(question_text.casefold().split()),
            " ".join(answer_text.casefold().split()),
        )
        evaluation = {
            "score": answer.score,
            "technical_accuracy": answer.technical_accuracy,
            "completeness": answer.completeness,
            "clarity": answer.clarity,
            "communication_score": answer.communication_score,
        }
        if key in records:
            records[key]["question_ids"].append(question.id)
            records[key]["evaluations"].append(evaluation)
            continue
        records[key] = {
            "question_ids": [question.id],
            "question": question_text,
            "answer": answer_text,
            "score": answer.score,
            "evaluations": [evaluation],
        }
    return list(records.values())


def _report_batches(records, interview_type, resume_context, jd_context):
    """Pack full answer segments into prompts below token, character, and body limits."""
    agent = coordinator.performance_agent
    batches = []
    current = []

    def prompt_fits(items):
        prompt = agent.build_prompt(items, interview_type, resume_context, jd_context)
        return prompt_within_limits(prompt, settings_model(), 2000)

    pending = []
    for record in records:
        answer_parts = split_text_preserving_content(record["answer"], REPORT_MAX_ANSWER_CHARS)
        for part_number, answer_part in enumerate(answer_parts, start=1):
            part = dict(record)
            part["answer"] = answer_part
            if len(answer_parts) > 1:
                part["answer_part"] = f"{part_number}/{len(answer_parts)}"
            pending.append(part)

    while pending:
        item = pending.pop(0)
        candidate = current + [item]
        if len(candidate) <= REPORT_MAX_BATCH_ANSWERS and prompt_fits(candidate):
            current = candidate
            continue
        if current:
            batches.append(current)
            current = []
            pending.insert(0, item)
            continue
        answer = item["answer"]
        if len(answer) <= 200:
            raise HTTPException(
                status_code=413,
                detail="Report context alone exceeds the configured Groq input limit. Reduce the report input limits or context.",
            )
        smaller_parts = split_text_preserving_content(answer, max(200, len(answer) // 2))
        if len(smaller_parts) < 2:
            raise HTTPException(status_code=413, detail="A report answer cannot fit within the configured Groq input limit.")
        for subpart in reversed(smaller_parts):
            smaller = dict(item)
            smaller["answer"] = subpart
            pending.insert(0, smaller)

    if current:
        batches.append(current)
    return batches


def settings_model():
    return settings.GROQ_MODEL


def _compact_analysis(analysis):
    return {
        "overall_score": analysis.get("overall_score"),
        "technical_score": analysis.get("technical_score"),
        "communication_score": analysis.get("communication_score"),
        "hiring_probability": analysis.get("hiring_probability"),
        "hiring_recommendation": analysis.get("hiring_recommendation"),
        "skill_matrix": analysis.get("skill_matrix", {}),
        "radar_chart_data": analysis.get("radar_chart_data", [])[:8],
        "strengths": analysis.get("strengths", [])[:5],
        "weaknesses": analysis.get("weaknesses", [])[:5],
        "topics_to_improve": analysis.get("topics_to_improve", [])[:5],
        "learning_recommendations": analysis.get("learning_recommendations", [])[:5],
        "ai_summary": (analysis.get("ai_summary") or "")[:1200],
    }


def _analyze_in_batches(records, interview_type, resume_context, jd_context):
    batches = _report_batches(records, interview_type, resume_context, jd_context)
    question_count = len({
        question_id
        for record in records
        for question_id in record.get("question_ids", [])
    })
    logger.info("Generating interview report question_count=%s batch_count=%s", question_count, len(batches))
    analyses = []
    for index, batch in enumerate(batches, start=1):
        logger.info("Analyzing interview report batch=%s/%s item_count=%s", index, len(batches), len(batch))
        analyses.append(coordinator.analyze_full_interview(
            answers_data=batch,
            interview_type=interview_type,
            resume_ctx=resume_context if index == 1 else "",
            jd_ctx=jd_context if index == 1 else "",
        ))

    while len(analyses) > 1:
        summaries = []
        for index, analysis in enumerate(analyses, start=1):
            summary = _compact_analysis(analysis)
            summary["batch_number"] = index
            summaries.append({
                "question_ids": [],
                "question": f"Interview analysis batch {index}",
                "answer": json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
                "score": analysis.get("overall_score"),
                "evaluations": [],
            })
        combined_batches = _report_batches(summaries, interview_type, "", "")
        combined = []
        for index, batch in enumerate(combined_batches, start=1):
            logger.info("Combining report summaries batch=%s/%s item_count=%s", index, len(combined_batches), len(batch))
            combined.append(coordinator.analyze_full_interview(
                answers_data=batch,
                interview_type=interview_type,
                resume_ctx="",
                jd_ctx="",
            ))
        analyses = combined
    return analyses[0]


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
