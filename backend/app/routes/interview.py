"""Interview session routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import User, InterviewSession, Question, Answer
from app.schemas.schemas import (
    InterviewSessionStart, InterviewSessionResponse, QuestionResponse,
    AnswerSubmit, AnswerResponse,
)
from app.utils.auth import get_current_user
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["interview"])


class GenerateQuestionBody(BaseModel):
    category: str = "Technical"
    difficulty: str = "MEDIUM"
    question_number: Optional[int] = None


class NextQuestionBody(BaseModel):
    current_question_id: Optional[int] = None
    action: str = "start"


class SkipQuestionBody(BaseModel):
    question_id: int


@router.post("/start", response_model=InterviewSessionResponse)
async def start_interview(
    session_data: InterviewSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new interview session"""
    metadata = dict(session_data.session_metadata or {})
    if metadata.get("company_mode") and not session_data.company:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A company is required for a company interview.",
        )
    for key in (
        "company", "role", "experience", "skills", "job_description",
        "interview_round", "question_count", "interview_duration_minutes",
    ):
        value = getattr(session_data, key, None)
        if value is not None:
            metadata[key] = value
    metadata["difficulty"] = session_data.difficulty
    metadata["category"] = session_data.category
    if metadata.get("company_mode"):
        metadata["monitoring_enabled"] = False
    return InterviewService.start_session(
        user_id=current_user.id,
        interview_type=session_data.interview_type,
        category=session_data.category,
        difficulty=session_data.difficulty,
        db=db,
        session_metadata=metadata,
    )


@router.post("/generate-question/{session_id}", response_model=QuestionResponse)
async def generate_question(
    session_id: int,
    body: GenerateQuestionBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a question for the interview session"""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")

    try:
        return InterviewService.generate_question(
            session_id=session_id,
            category=body.category,
            difficulty=body.difficulty,
            question_number=body.question_number,
            db=db,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/next-question/{session_id}", response_model=QuestionResponse)
async def get_next_question(
    session_id: int,
    body: NextQuestionBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Idempotently retrieve or generate the next question in session order."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")

    try:
        return InterviewService.next_question(
            session_id=session_id,
            current_question_id=body.current_question_id,
            action=body.action,
            db=db,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/skip-question/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def skip_question(
    session_id: int,
    body: SkipQuestionBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    InterviewService.skip_question(session_id, body.question_id, db)


@router.post("/submit-answer", response_model=AnswerResponse)
async def submit_answer(
    answer_data: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit answer and get AI evaluation"""
    question = (
        db.query(Question)
        .filter(Question.id == answer_data.question_id)
        .join(InterviewSession)
        .filter(InterviewSession.user_id == current_user.id)
        .first()
    )

    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    return InterviewService.submit_answer(
        question_id=answer_data.question_id,
        user_answer=answer_data.user_answer,
        db=db,
    )


@router.post("/end/{session_id}", response_model=InterviewSessionResponse)
async def end_interview(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """End interview session and compute final score"""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")

    return InterviewService.end_session(session_id=session_id, db=db)


@router.get("/session/{session_id}", response_model=InterviewSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    return session


@router.get("/questions/{session_id}")
async def get_session_questions(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    questions = db.query(Question).filter(Question.session_id == session_id).order_by(Question.id).all()
    metadata = session.session_metadata or {}
    details = metadata.get("question_details", {})
    total_questions = metadata.get("question_count")
    skipped_ids = metadata.get("skipped_question_ids") or []
    response = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question.question_text, str) or not question.question_text.strip():
            question = InterviewService.generate_question(
                session_id=session_id,
                category=question.category,
                difficulty=question.difficulty,
                question_number=index,
                db=db,
            )
            metadata = session.session_metadata or {}
            details = metadata.get("question_details", {})
        item = QuestionResponse.model_validate(question)
        item.question_id = question.id
        detail = details.get(str(question.id), {})
        response.append(item.model_copy(update={
            "question_number": index,
            "total_questions": total_questions,
            "topic": detail.get("topic"),
            "context": detail.get("context"),
            "evaluation_criteria": detail.get("evaluation_criteria"),
            "company_specific": detail.get("company_specific"),
            "question": question.question_text,
            "status": "answered" if question.answers else "skipped" if question.id in skipped_ids else "in_progress",
            "is_answered": bool(question.answers),
            "is_skipped": question.id in skipped_ids,
        }))
    return response


@router.get("/answer/{answer_id}", response_model=AnswerResponse)
async def get_answer(
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer = (
        db.query(Answer)
        .filter(Answer.id == answer_id)
        .join(Question)
        .join(InterviewSession)
        .filter(InterviewSession.user_id == current_user.id)
        .first()
    )
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    return answer
