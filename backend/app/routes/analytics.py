"""Analytics and history routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import User, InterviewSession, Analytics, InterviewReport, Answer, Question
from app.schemas.schemas import (
    AnalyticsResponse, InterviewHistoryResponse, InterviewHistoryItem,
    InterviewReportResponse
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user analytics and statistics"""
    
    # Get or create analytics record
    analytics = db.query(Analytics).filter(
        Analytics.user_id == current_user.id
    ).first()
    
    if not analytics:
        analytics = Analytics(user_id=current_user.id)
        db.add(analytics)
    
    # Calculate statistics
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == "COMPLETED"
    ).all()
    
    if sessions:
        analytics.total_interviews = len(sessions)
        scores = [s.overall_score for s in sessions if s.overall_score]
        
        if scores:
            analytics.average_score = sum(scores) / len(scores)
            analytics.best_score = max(scores)
            analytics.worst_score = min(scores)
    
    # Calculate category-based scores
    answers = db.query(Answer).join(Question).join(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).all()
    
    if answers:
        # Calculate different metric scores
        technical_scores = [a.technical_accuracy for a in answers if a.technical_accuracy]
        communication_scores = [a.communication_score for a in answers if a.communication_score]
        
        if technical_scores:
            analytics.technical_score = sum(technical_scores) / len(technical_scores)
        if communication_scores:
            analytics.communication_score = sum(communication_scores) / len(communication_scores)
    
    db.commit()
    db.refresh(analytics)
    
    return analytics


@router.get("/history")
async def get_interview_history(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview history"""
    
    total_count = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).count()
    
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.started_at.desc()).offset(skip).limit(limit).all()
    
    history_items = [
        InterviewHistoryItem(
            id=s.id,
            interview_type=s.interview_type,
            overall_score=s.overall_score,
            started_at=s.started_at,
            completed_at=s.completed_at,
            duration_minutes=s.duration_minutes,
            status=s.status
        )
        for s in sessions
    ]
    
    return InterviewHistoryResponse(
        total_count=total_count,
        interviews=history_items
    )


@router.get("/report/{session_id}", response_model=InterviewReportResponse)
async def get_session_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get report for a completed interview session"""
    
    report = db.query(InterviewReport).filter(
        InterviewReport.session_id == session_id,
        InterviewReport.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report


@router.get("/strengths-weaknesses")
async def get_strengths_weaknesses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get identified strengths and weaknesses"""
    
    analytics = db.query(Analytics).filter(
        Analytics.user_id == current_user.id
    ).first()
    
    if not analytics:
        return {
            "strengths": [],
            "weaknesses": [],
            "recommended_focus": []
        }
    
    return {
        "strengths": analytics.strengths or [],
        "weaknesses": analytics.weaknesses or [],
        "weak_areas": analytics.weak_areas or [],
        "topics_covered": analytics.topics_covered or []
    }


@router.get("/performance-trend")
async def get_performance_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance trend over time"""
    
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == "COMPLETED"
    ).order_by(InterviewSession.completed_at).all()
    
    trend_data = [
        {
            "date": s.completed_at.isoformat() if s.completed_at else s.started_at.isoformat(),
            "score": s.overall_score,
            "interview_type": s.interview_type
        }
        for s in sessions
    ]
    
    return {
        "trend": trend_data,
        "total_sessions": len(sessions)
    }


@router.get("/category-performance")
async def get_category_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance by category"""
    
    answers = db.query(
        Question.category,
        func.count(Question.id).label("count"),
        func.avg(Answer.score).label("avg_score"),
        func.max(Answer.score).label("max_score"),
        func.min(Answer.score).label("min_score")
    ).join(Question).join(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).group_by(Question.category).all()
    
    category_stats = [
        {
            "category": row[0],
            "questions_answered": row[1],
            "average_score": float(row[2]) if row[2] else 0,
            "max_score": float(row[3]) if row[3] else 0,
            "min_score": float(row[4]) if row[4] else 0
        }
        for row in answers
    ]
    
    return {"categories": category_stats}
