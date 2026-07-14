"""ATS Resume Analyzer routes"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models.models import User, ATSReport, Resume
from app.utils.auth import get_current_user
from app.services.ats_service import analyze_ats, generate_ats_pdf

router = APIRouter(prefix="/ats", tags=["ats"])


class ATSRequest(BaseModel):
    jd_text: str
    resume_id: Optional[int] = None
    resume_text: Optional[str] = None


@router.post("/analyze")
async def analyze(
    body: ATSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume_text = body.resume_text or ""
    resume_id = body.resume_id

    if not resume_text and resume_id:
        resume = db.query(Resume).filter(
            Resume.id == resume_id, Resume.user_id == current_user.id
        ).first()
        if resume and resume.resume_text:
            resume_text = resume.resume_text

    if not resume_text:
        resume = db.query(Resume).filter(
            Resume.user_id == current_user.id
        ).order_by(Resume.uploaded_at.desc()).first()
        if resume and resume.resume_text:
            resume_text = resume.resume_text
            resume_id = resume.id

    if not resume_text:
        raise HTTPException(status_code=400, detail="No resume text found. Please upload a resume first.")

    result = analyze_ats(resume_text, body.jd_text)

    report = ATSReport(
        user_id=current_user.id,
        resume_id=resume_id,
        jd_text=body.jd_text[:2000],
        ats_score=result.get("ats_score"),
        keyword_match_pct=result.get("keyword_match_pct"),
        matching_skills=result.get("matching_skills"),
        missing_skills=result.get("missing_skills"),
        missing_technologies=result.get("missing_technologies"),
        strengths=result.get("strengths"),
        weaknesses=result.get("weaknesses"),
        improvements=result.get("improvements"),
        formatting_suggestions=result.get("formatting_suggestions"),
        ai_summary=result.get("ai_summary"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        pdf_path = generate_ats_pdf(result, current_user.name, report.id)
        report.pdf_path = pdf_path
        db.commit()
    except Exception:
        pass

    return {**result, "report_id": report.id, "has_pdf": bool(report.pdf_path)}


@router.get("/reports")
async def get_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reports = db.query(ATSReport).filter(
        ATSReport.user_id == current_user.id
    ).order_by(ATSReport.created_at.desc()).limit(10).all()
    return [
        {
            "id": r.id, "ats_score": r.ats_score,
            "keyword_match_pct": r.keyword_match_pct,
            "matching_skills": r.matching_skills,
            "missing_skills": r.missing_skills,
            "ai_summary": r.ai_summary,
            "created_at": r.created_at.isoformat(),
            "has_pdf": bool(r.pdf_path),
        }
        for r in reports
    ]


@router.get("/report/{report_id}/pdf")
async def download_pdf(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(ATSReport).filter(
        ATSReport.id == report_id, ATSReport.user_id == current_user.id
    ).first()
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not available.")
    return FileResponse(report.pdf_path, media_type="application/pdf", filename=f"ats_report_{report_id}.pdf")
