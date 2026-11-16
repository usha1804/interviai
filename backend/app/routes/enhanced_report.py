"""Enhanced interview report routes"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models.models import User, EnhancedInterviewReport, InterviewSession, Question
from app.utils.auth import get_current_user
from app.services.report_service import generate_enhanced_report

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate/{session_id}")
async def generate_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    report = generate_enhanced_report(session_id, current_user.id, db)
    return _serialize(report, db)


@router.get("/{session_id}")
async def get_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(EnhancedInterviewReport).filter(
        EnhancedInterviewReport.session_id == session_id,
        EnhancedInterviewReport.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Generate it first.")
    return _serialize(report, db)


@router.get("/{session_id}/pdf")
async def download_pdf(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(EnhancedInterviewReport).filter(
        EnhancedInterviewReport.session_id == session_id,
        EnhancedInterviewReport.user_id == current_user.id,
    ).first()
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not available.")
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"interview_report_{session_id}.pdf",
    )


def _serialize(r: EnhancedInterviewReport, db: Session) -> dict:
    questions = db.query(Question).filter(
        Question.session_id == r.session_id
    ).order_by(Question.id).all()
    return {
        "id": r.id,
        "session_id": r.session_id,
        "technical_score": r.technical_score,
        "communication_score": r.communication_score,
        "coding_score": r.coding_score,
        "confidence_score": r.confidence_score,
        "overall_score": r.overall_score,
        "hiring_probability": r.hiring_probability,
        "hiring_recommendation": r.hiring_recommendation,
        "skill_matrix": r.skill_matrix,
        "radar_chart_data": r.radar_chart_data,
        "strengths": r.strengths,
        "weaknesses": r.weaknesses,
        "topics_to_improve": r.topics_to_improve,
        "learning_recommendations": r.learning_recommendations,
        "ai_summary": r.ai_summary,
        "question_feedback": [
            {
                "question": question.question_text,
                "category": question.category,
                "difficulty": question.difficulty,
                "answer": answer.user_answer,
                "score": answer.score,
                "technical_accuracy": answer.technical_accuracy,
                "completeness": answer.completeness,
                "clarity": answer.clarity,
                "communication_score": answer.communication_score,
                "feedback": answer.ai_feedback,
                "strengths": answer.strengths,
                "improvements": answer.improvements,
            }
            for question in questions
            for answer in question.answers
        ],
        "has_pdf": bool(r.pdf_path),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
