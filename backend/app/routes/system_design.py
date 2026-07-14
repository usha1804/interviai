"""System Design Interview routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, SystemDesignSession
from app.utils.auth import get_current_user
from app.services.system_design_service import (
    generate_system_design_questions,
    evaluate_system_design_answer,
    generate_final_system_design_report,
    SYSTEM_DESIGN_TOPICS,
)

router = APIRouter(prefix="/system-design", tags=["system-design"])


class StartRequest(BaseModel):
    topic: str
    difficulty: str = "MEDIUM"


class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_index: int
    answer: str


@router.get("/topics")
async def get_topics():
    return {"topics": list(SYSTEM_DESIGN_TOPICS.keys())}


@router.post("/start")
async def start_session(
    body: StartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.topic not in SYSTEM_DESIGN_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {body.topic}")

    questions = generate_system_design_questions(body.topic, body.difficulty)
    session = SystemDesignSession(
        user_id=current_user.id,
        topic=body.topic,
        difficulty=body.difficulty,
        questions=questions,
        answers=[],
        status="IN_PROGRESS",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "topic": session.topic, "questions": questions}


@router.post("/submit-answer")
async def submit_answer(
    body: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(SystemDesignSession).filter(
        SystemDesignSession.id == body.session_id,
        SystemDesignSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    questions = session.questions or []
    if body.question_index >= len(questions):
        raise HTTPException(status_code=400, detail="Invalid question index.")

    q = questions[body.question_index]
    evaluation = evaluate_system_design_answer(
        topic=session.topic,
        question=q["question"],
        answer=body.answer,
        question_category=q.get("category", "General"),
    )

    answers = list(session.answers or [])
    answers.append({
        "question_index": body.question_index,
        "question": q["question"],
        "answer": body.answer,
        "score": evaluation.get("overall_score", 5),
        "evaluation": evaluation,
    })
    session.answers = answers
    db.commit()

    return {"evaluation": evaluation, "answer_index": len(answers) - 1}


@router.post("/end/{session_id}")
async def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(SystemDesignSession).filter(
        SystemDesignSession.id == session_id,
        SystemDesignSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    report = generate_final_system_design_report(session.topic, session.answers or [])

    session.overall_score = report.get("overall_score")
    session.architecture_score = report.get("architecture_score")
    session.scalability_score = report.get("scalability_score")
    session.tradeoffs_score = report.get("tradeoffs_score")
    session.ai_feedback = report
    session.status = "COMPLETED"
    session.completed_at = datetime.utcnow()
    db.commit()

    return {"session_id": session_id, "report": report}


@router.get("/session/{session_id}")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(SystemDesignSession).filter(
        SystemDesignSession.id == session_id,
        SystemDesignSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "id": session.id, "topic": session.topic, "difficulty": session.difficulty,
        "questions": session.questions, "answers": session.answers,
        "overall_score": session.overall_score, "status": session.status,
        "ai_feedback": session.ai_feedback,
    }
