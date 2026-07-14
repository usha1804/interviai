"""Admin routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import User, InterviewSession, AIPrompt
from app.schemas.schemas import UserListResponse, UserResponse, SessionStatisticsResponse
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    
    total_count = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()
    
    return UserListResponse(
        total_count=total_count,
        users=users
    )


@router.get("/statistics", response_model=SessionStatisticsResponse)
async def get_statistics(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get platform statistics (admin only)"""
    
    total_sessions = db.query(InterviewSession).count()
    completed_sessions = db.query(InterviewSession).filter(
        InterviewSession.status == "COMPLETED"
    ).count()
    
    avg_score_result = db.query(
        func.avg(InterviewSession.overall_score)
    ).filter(InterviewSession.status == "COMPLETED").first()
    
    average_score = float(avg_score_result[0]) if avg_score_result[0] else 0
    
    most_common_type = db.query(
        InterviewSession.interview_type,
        func.count(InterviewSession.id)
    ).group_by(InterviewSession.interview_type).order_by(
        func.count(InterviewSession.id).desc()
    ).first()
    
    most_common_category = "TECHNICAL"  # Can be extended based on Questions table
    
    return SessionStatisticsResponse(
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        average_score=average_score,
        most_common_type=most_common_type[0] if most_common_type else "TECHNICAL",
        most_common_category=most_common_category
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user details (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/ai-prompts")
async def list_ai_prompts(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List AI prompts (admin only)"""
    
    prompts = db.query(AIPrompt).filter(AIPrompt.is_active == True).all()
    
    return {
        "total_count": len(prompts),
        "prompts": prompts
    }


@router.post("/ai-prompts")
async def create_ai_prompt(
    prompt_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create AI prompt (admin only)"""
    
    new_prompt = AIPrompt(
        name=prompt_data.get("name"),
        category=prompt_data.get("category"),
        prompt_template=prompt_data.get("prompt_template"),
        metadata=prompt_data.get("metadata", {})
    )
    
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    
    return new_prompt


@router.get("/sessions")
async def list_sessions(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all interview sessions (admin only)"""
    
    total_count = db.query(InterviewSession).count()
    sessions = db.query(InterviewSession).offset(skip).limit(limit).all()
    
    return {
        "total_count": total_count,
        "sessions": sessions
    }
