"""Career Coach routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, CareerProfile, Resume, JobDescription
from app.utils.auth import get_current_user
from app.services.career_coach_service import analyze_career

router = APIRouter(prefix="/career-coach", tags=["career-coach"])


class CareerAnalyzeRequest(BaseModel):
    resume_id: Optional[int] = None
    jd_id: Optional[int] = None
    interview_score: Optional[float] = None
    coding_score: Optional[float] = None
    communication_score: Optional[float] = None


@router.post("/analyze")
async def analyze(
    body: CareerAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run full career coach analysis."""
    resume = None
    if body.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == body.resume_id, Resume.user_id == current_user.id
        ).first()
    else:
        resume = db.query(Resume).filter(
            Resume.user_id == current_user.id
        ).order_by(Resume.uploaded_at.desc()).first()

    jd = None
    if body.jd_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == body.jd_id, JobDescription.user_id == current_user.id
        ).first()
    else:
        jd = db.query(JobDescription).filter(
            JobDescription.user_id == current_user.id
        ).order_by(JobDescription.uploaded_at.desc()).first()

    resume_text = resume.resume_text or "" if resume else ""
    jd_text = jd.content if jd else ""

    result = analyze_career(
        user_id=current_user.id,
        resume_text=resume_text,
        jd_text=jd_text,
        interview_score=body.interview_score,
        coding_score=body.coding_score,
        communication_score=body.communication_score,
    )

    # Persist
    profile = db.query(CareerProfile).filter(
        CareerProfile.user_id == current_user.id
    ).order_by(CareerProfile.created_at.desc()).first()

    if not profile:
        profile = CareerProfile(
            user_id=current_user.id,
            resume_id=resume.id if resume else None,
            jd_id=jd.id if jd else None,
        )
        db.add(profile)

    profile.resume_match_score = result.get("resume_match_score")
    profile.job_match_score = result.get("job_match_score")
    profile.hiring_probability = result.get("hiring_probability")
    profile.interview_readiness = result.get("interview_readiness")
    profile.current_skills = result.get("current_skills")
    profile.missing_skills = result.get("missing_skills")
    profile.skill_gap_analysis = result.get("skill_gap_analysis")
    profile.recommended_courses = result.get("recommended_courses")
    profile.recommended_certifications = result.get("recommended_certifications")
    profile.recommended_projects = result.get("recommended_projects")
    profile.learning_plan_30 = result.get("learning_plan_30")
    profile.learning_plan_60 = result.get("learning_plan_60")
    profile.learning_plan_90 = result.get("learning_plan_90")
    profile.ai_summary = result.get("ai_summary")
    db.commit()
    db.refresh(profile)

    return {**result, "profile_id": profile.id}


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CareerProfile).filter(
        CareerProfile.user_id == current_user.id
    ).order_by(CareerProfile.created_at.desc()).first()
    if not profile:
        return {"profile": None}
    return {
        "profile": {
            "resume_match_score": profile.resume_match_score,
            "job_match_score": profile.job_match_score,
            "hiring_probability": profile.hiring_probability,
            "interview_readiness": profile.interview_readiness,
            "current_skills": profile.current_skills,
            "missing_skills": profile.missing_skills,
            "skill_gap_analysis": profile.skill_gap_analysis,
            "recommended_courses": profile.recommended_courses,
            "recommended_certifications": profile.recommended_certifications,
            "recommended_projects": profile.recommended_projects,
            "learning_plan_30": profile.learning_plan_30,
            "learning_plan_60": profile.learning_plan_60,
            "learning_plan_90": profile.learning_plan_90,
            "ai_summary": profile.ai_summary,
        }
    }


@router.get("/skill-gap")
async def get_skill_gap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CareerProfile).filter(
        CareerProfile.user_id == current_user.id
    ).order_by(CareerProfile.created_at.desc()).first()
    if not profile:
        return {"skill_gap": {}, "missing_skills": [], "current_skills": []}
    return {
        "skill_gap": profile.skill_gap_analysis or {},
        "missing_skills": profile.missing_skills or [],
        "current_skills": profile.current_skills or [],
    }


@router.get("/learning-plan/{days}")
async def get_learning_plan(
    days: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if days not in (30, 60, 90):
        raise HTTPException(status_code=400, detail="days must be 30, 60, or 90")
    profile = db.query(CareerProfile).filter(
        CareerProfile.user_id == current_user.id
    ).order_by(CareerProfile.created_at.desc()).first()
    if not profile:
        return {"plan": None}
    plan = getattr(profile, f"learning_plan_{days}")
    return {"days": days, "plan": plan}
