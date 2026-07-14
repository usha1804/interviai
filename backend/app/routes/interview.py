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


@router.post("/start", response_model=InterviewSessionResponse)
async def start_interview(
    session_data: InterviewSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new interview session"""
    return InterviewService.start_session(
        user_id=current_user.id,
        interview_type=session_data.interview_type,
        category=session_data.category,
        difficulty=session_data.difficulty,
        db=db,
        session_metadata=session_data.session_metadata,
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

    return InterviewService.generate_question(
        session_id=session_id,
        category=body.category,
        difficulty=body.difficulty,
        db=db,
    )


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
    return db.query(Question).filter(Question.session_id == session_id).all()


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
