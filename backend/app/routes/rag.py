"""RAG pipeline routes"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, JobDescription, Resume
from app.utils.auth import get_current_user
from app.services.rag_service import (
    ingest_resume, ingest_job_description,
    generate_rag_questions, evaluate_answer_with_context,
)
from app.services.company_rag_service import ingest_company_document, SUPPORTED_COMPANIES
from app.services.memory_service import get_asked_questions, get_next_difficulty

router = APIRouter(prefix="/rag", tags=["rag"])


class JDUploadRequest(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    content: str


class RAGGenerateRequest(BaseModel):
    question_types: List[str] = ["Technical", "Project", "Behavioral", "Scenario"]
    difficulty: Optional[str] = None
    company: Optional[str] = None


class RAGEvalRequest(BaseModel):
    question: str
    answer: str
    category: str


class CompanyIngestRequest(BaseModel):
    company: str
    content: str
    source: Optional[str] = "manual"


@router.get("/companies")
async def list_supported_companies():
    return {"companies": SUPPORTED_COMPANIES}


@router.post("/company/ingest")
async def ingest_company_document_endpoint(
    body: CompanyIngestRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return ingest_company_document(body.company, body.content, body.source)


@router.post("/upload-jd")
async def upload_job_description(
    body: JDUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store a job description and ingest into ChromaDB."""
    jd = JobDescription(
        user_id=current_user.id,
        title=body.title,
        company=body.company,
        content=body.content,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)

    ingest_job_description(current_user.id, jd.id, body.content)
    return {"id": jd.id, "message": "Job description uploaded and indexed."}


@router.get("/jd")
async def get_jd(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = db.query(JobDescription).filter(
        JobDescription.user_id == current_user.id
    ).order_by(JobDescription.uploaded_at.desc()).first()
    if not jd:
        return {"jd": None}
    return {"jd": {"id": jd.id, "title": jd.title, "company": jd.company, "content": jd.content[:500]}}


@router.post("/generate-questions")
async def generate_questions(
    body: RAGGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate RAG-grounded interview questions."""
    asked = get_asked_questions(current_user.id, db)
    difficulty = body.difficulty or get_next_difficulty(current_user.id, db)

    result = generate_rag_questions(
        user_id=current_user.id,
        question_types=body.question_types,
        difficulty=difficulty,
        company=body.company,
        asked_questions=asked,
    )
    return result


@router.post("/evaluate")
async def evaluate_answer(
    body: RAGEvalRequest,
    current_user: User = Depends(get_current_user),
):
    """Evaluate answer using RAG context."""
    result = evaluate_answer_with_context(
        user_id=current_user.id,
        question=body.question,
        user_answer=body.answer,
        category=body.category,
    )
    return result


@router.post("/ingest-resume/{resume_id}")
async def ingest_resume_endpoint(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-ingest a resume into ChromaDB (called after upload)."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume or not resume.resume_text:
        raise HTTPException(status_code=404, detail="Resume not found or not parsed.")
    ingest_resume(current_user.id, resume_id, resume.resume_text)
    return {"message": "Resume indexed successfully."}
