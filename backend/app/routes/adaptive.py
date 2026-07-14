"""Adaptive Interview Engine routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, InterviewSession, Question, Answer
from app.utils.auth import get_current_user
from app.services.adaptive_engine import (
    get_adaptive_params, generate_adaptive_question, DIFFICULTY_LADDER
)
from app.services.memory_service import (
    get_or_create, get_asked_questions, record_question,
    record_answer_score, get_next_difficulty
)
from app.services.rag_service import retrieve_resume_context

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


class AdaptiveNextRequest(BaseModel):
    session_id: int
    category: str
    company: Optional[str] = None


class AdaptiveSubmitRequest(BaseModel):
    session_id: int
    question_id: int
    user_answer: str


@router.post("/next-question")
async def next_question(
    body: AdaptiveNextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate the next adaptive question based on performance history."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == body.session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Get all scores so far in this session
    answers = db.query(Answer).join(Question).filter(
        Question.session_id == body.session_id
    ).all()
    session_scores = [a.score for a in answers if a.score is not None]

    mem = get_or_create(current_user.id, db)
    current_diff = mem.last_difficulty or "MEDIUM"

    params = get_adaptive_params(
        session_scores=session_scores,
        current_difficulty=current_diff,
        interview_type=session.interview_type,
        weak_topics=mem.weak_topics or [],
    )

    resume_ctx = retrieve_resume_context(current_user.id, body.category, k=2)
    asked = get_asked_questions(current_user.id, db)

    question_text = generate_adaptive_question(
        category=body.category,
        difficulty=params["next_difficulty"],
        question_type=params["next_question_type"],
        asked_questions=asked,
        weak_topics=mem.weak_topics or [],
        strong_topics=mem.strong_topics or [],
        resume_context=resume_ctx,
        company=body.company,
    )

    # Save question
    q = Question(
        session_id=body.session_id,
        question_text=question_text,
        category=body.category,
        difficulty=params["next_difficulty"],
        question_type=params["next_question_type"],
    )
    db.add(q)

    # Update memory difficulty
    mem.last_difficulty = params["next_difficulty"]
    db.commit()
    db.refresh(q)

    record_question(current_user.id, question_text, db)

    return {
        "question": {
            "id": q.id,
            "question_text": q.question_text,
            "category": q.category,
            "difficulty": q.difficulty,
            "question_type": q.question_type,
        },
        "adaptive_info": params,
    }


@router.post("/submit-answer")
async def submit_answer(
    body: AdaptiveSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit answer — evaluate and update adaptive state."""
    from app.services.ai_service import ai_service

    question = db.query(Question).filter(Question.id == body.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    evaluation = ai_service.evaluate_answer(
        question=question.question_text,
        user_answer=body.user_answer,
        category=question.category,
        difficulty=question.difficulty,
    )

    answer = Answer(
        question_id=body.question_id,
        user_answer=body.user_answer,
        score=evaluation.get("score"),
        technical_accuracy=evaluation.get("technical_accuracy"),
        completeness=evaluation.get("completeness"),
        clarity=evaluation.get("clarity"),
        communication_score=evaluation.get("communication_score"),
        ai_feedback=evaluation.get("feedback"),
        strengths=evaluation.get("strengths"),
        improvements=evaluation.get("improvements"),
        ideal_answer=evaluation.get("ideal_answer"),
        evaluation_metadata=evaluation,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)

    record_answer_score(current_user.id, question.category, evaluation.get("score", 5), db)

    return {
        "answer_id": answer.id,
        "score": answer.score,
        "feedback": answer.ai_feedback,
        "ideal_answer": answer.ideal_answer,
        "strengths": answer.strengths,
        "improvements": answer.improvements,
        "evaluation": evaluation,
    }
