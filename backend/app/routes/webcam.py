"""Webcam behavior analysis routes"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, InterviewBehavior
from app.utils.auth import get_current_user
from app.services.webcam_service import compute_scores, generate_behavior_feedback

router = APIRouter(prefix="/webcam", tags=["webcam"])


class FrameMetrics(BaseModel):
    """Aggregated metrics sent from the frontend after a session."""
    session_id: str
    eye_contact_pct: float = 70
    attention_pct: float = 70
    movement_score: float = 30      # lower = less movement = better
    smile_pct: float = 40
    duration_seconds: Optional[int] = None


class BehaviorReport(BaseModel):
    session_id: str
    confidence_score: float
    eye_contact_score: float
    posture_score: float
    expression_score: float
    ai_feedback: dict
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/analyze", response_model=BehaviorReport)
async def analyze_behavior(
    metrics: FrameMetrics,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive aggregated webcam metrics, compute scores, generate AI feedback, persist."""
    scores = compute_scores(metrics.dict())
    feedback = generate_behavior_feedback(scores)

    record = InterviewBehavior(
        user_id=current_user.id,
        session_id=metrics.session_id,
        confidence_score=scores["confidence_score"],
        eye_contact_score=scores["eye_contact_score"],
        posture_score=scores["posture_score"],
        expression_score=scores["expression_score"],
        ai_feedback=feedback,
        raw_metrics=metrics.dict(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return BehaviorReport(
        session_id=record.session_id,
        confidence_score=record.confidence_score,
        eye_contact_score=record.eye_contact_score,
        posture_score=record.posture_score,
        expression_score=record.expression_score,
        ai_feedback=record.ai_feedback,
        created_at=record.created_at,
    )


@router.get("/report/{session_id}", response_model=BehaviorReport)
async def get_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(InterviewBehavior).filter(
        InterviewBehavior.session_id == session_id,
        InterviewBehavior.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Behavior report not found.")
    return BehaviorReport(
        session_id=record.session_id,
        confidence_score=record.confidence_score,
        eye_contact_score=record.eye_contact_score,
        posture_score=record.posture_score,
        expression_score=record.expression_score,
        ai_feedback=record.ai_feedback,
        created_at=record.created_at,
    )


@router.get("/history", response_model=List[BehaviorReport])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(InterviewBehavior)
        .filter(InterviewBehavior.user_id == current_user.id)
        .order_by(InterviewBehavior.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        BehaviorReport(
            session_id=r.session_id,
            confidence_score=r.confidence_score,
            eye_contact_score=r.eye_contact_score,
            posture_score=r.posture_score,
            expression_score=r.expression_score,
            ai_feedback=r.ai_feedback,
            created_at=r.created_at,
        )
        for r in records
    ]
