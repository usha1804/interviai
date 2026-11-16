"""Resume upload and management routes"""
import os
from datetime import datetime
from typing import List
from uuid import uuid4
import zipfile
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Resume, User
from app.schemas.schemas import ResumeResponse, ResumeQuestionRequest, ResumeQuestionSet
from app.utils.auth import get_current_user
from app.services.resume_service import (
    extract_text, parse_resume_with_ai, generate_resume_questions,
)

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = "uploads/resumes"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"pdf", "docx"}


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a resume (PDF/DOCX), extract text, parse with AI, save to DB."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext or 'unknown'} not allowed. Upload PDF or DOCX."
        )

    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit.")

    if ext == "pdf" and b"%PDF-" not in file_bytes[:1024]:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
    if ext == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("Missing Word document content.")
        except (zipfile.BadZipFile, ValueError):
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid DOCX document.")

    resume_text = extract_text(file_bytes, file.content_type or "", filename)
    if not resume_text or not resume_text.strip():
        message = (
            "No text could be extracted from this PDF. It may be scanned or image-only; "
            "upload a searchable PDF or DOCX."
            if ext == "pdf"
            else "No text could be extracted from this DOCX. Check that it contains readable text."
        )
        raise HTTPException(status_code=422, detail=message)

    parsed = parse_resume_with_ai(resume_text)

    _ensure_upload_dir()
    safe_name = os.path.basename(filename.replace("\\", "/")).replace(" ", "_")
    stored_name = f"{current_user.id}_{datetime.utcnow():%Y%m%d%H%M%S%f}_{uuid4().hex[:8]}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as uploaded_file:
        uploaded_file.write(file_bytes)

    resume = Resume(
        user_id=current_user.id,
        file_name=os.path.basename(filename.replace("\\", "/")),
        file_path=file_path,
        resume_text=resume_text,
        skills=parsed.get("skills", []) + parsed.get("technologies", []),
        projects=parsed.get("projects", []),
        experience=parsed.get("experience", []),
        education=parsed.get("education", []),
        parsed_data=parsed,
    )
    db.add(resume)
    try:
        db.commit()
        db.refresh(resume)
    except Exception:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    return resume


@router.get("/latest", response_model=ResumeResponse)
async def get_latest_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.user_id == current_user.id,
            Resume.resume_text.is_not(None),
            func.trim(Resume.resume_text) != "",
        )
        .order_by(Resume.uploaded_at.desc(), Resume.id.desc())
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No resume with extractable text found. Upload a searchable PDF or DOCX.",
        )
    return resume


@router.get("/all", response_model=List[ResumeResponse])
async def get_all_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc(), Resume.id.desc())
        .all()
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    # Remove file from disk
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)

    db.delete(resume)
    db.commit()


@router.post("/generate-questions", response_model=ResumeQuestionSet)
async def generate_questions(
    body: ResumeQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate interview questions based on a specific resume."""
    resume = db.query(Resume).filter(
        Resume.id == body.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    questions = generate_resume_questions(
        parsed_data=resume.parsed_data or {},
        difficulty=body.difficulty,
    )
    return questions


from pydantic import BaseModel as _BM

class EvaluateAnswerBody(_BM):
    question: str
    user_answer: str
    category: str
    resume_context: str = ""


@router.post("/evaluate-answer")
async def evaluate_resume_answer(
    body: EvaluateAnswerBody,
    current_user: User = Depends(get_current_user),
):
    """Evaluate a resume-interview answer with resume context."""
    from app.services.ai_service import _chat, get_groq_client
    from app.config import settings
    import json

    client = get_groq_client()
    prompt = f"""You are an expert technical interviewer evaluating a candidate's answer.

Resume Context: {body.resume_context}
Question: {body.question}
Category: {body.category}
Candidate's Answer: {body.user_answer}

Evaluate on Technical Accuracy, Completeness, Clarity, Communication (each 0-10).

Return ONLY this JSON:
{{
    "score": <0-10>,
    "technical_accuracy": <0-10>,
    "completeness": <0-10>,
    "clarity": <0-10>,
    "communication_score": <0-10>,
    "ai_feedback": "<2-3 sentence feedback>",
    "strengths": "<key strength>",
    "improvements": "<area to improve>",
    "ideal_answer": "<3-5 sentence model answer>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=800)
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "score": 6.0, "technical_accuracy": 6.0, "completeness": 6.0,
            "clarity": 6.0, "communication_score": 6.0,
            "ai_feedback": "Good attempt. Keep practising.",
            "strengths": "Attempted the question.",
            "improvements": "Add more specific examples.",
            "ideal_answer": "Refer to documentation for a complete answer.",
        }
