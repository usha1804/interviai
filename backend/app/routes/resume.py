"""Resume upload and management routes"""
import os
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Resume, User
from app.schemas.schemas import ResumeResponse, ResumeQuestionRequest, ResumeQuestionSet
from app.utils.auth import get_current_user
from app.services.resume_service import extract_text, parse_resume_with_ai, generate_resume_questions

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = "uploads/resumes"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a resume (PDF/DOCX), extract text, parse with AI, save to DB."""
    # Validate extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext} not allowed. Upload PDF or DOCX."
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit.")

    # Save file to disk
    _ensure_upload_dir()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{current_user.id}_{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract raw text
    resume_text = extract_text(file_bytes, file.content_type or "", file.filename)

    # AI parse
    parsed = parse_resume_with_ai(resume_text)

    # Save to DB
    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        resume_text=resume_text,
        skills=parsed.get("skills", []) + parsed.get("technologies", []),
        projects=parsed.get("projects", []),
        experience=parsed.get("experience", []),
        education=parsed.get("education", []),
        parsed_data=parsed,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/latest", response_model=ResumeResponse)
async def get_latest_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload one.")
    return resume


@router.get("/all", response_model=List[ResumeResponse])
async def get_all_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
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
    from app.services.ai_service import _chat
    from app.config import settings
    from groq import Groq
    import json

    client = Groq(api_key=settings.GROQ_API_KEY)
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
