"""Adaptive Interview Engine routes"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, InterviewSession, Question, Answer
from app.utils.auth import get_current_user
from app.services.adaptive_engine import get_adaptive_params, generate_adaptive_question
from app.services.memory_service import (
    get_or_create,
    get_asked_questions,
    record_question,
    record_answer_score,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/adaptive", tags=["adaptive"])


def retrieve_resume_context(user_id: int, query: str, k: int = 2) -> str:
    from app.services.rag_service import retrieve_resume_context as retrieve_context
    return retrieve_context(user_id, query, k=k)


class AdaptiveNextRequest(BaseModel):
    session_id: int
    category: str
    company: Optional[str] = None
    current_question_id: Optional[int] = None


class AdaptiveSubmitRequest(BaseModel):
    session_id: int
    question_id: int
    user_answer: str = Field(..., min_length=10)


def _question_response(question: Question, question_number: int, total_questions: int, params: dict) -> dict:
    return {
        "question": {
            "id": question.id,
            "session_id": question.session_id,
            "question_number": question_number,
            "total_questions": total_questions,
            "question_text": question.question_text,
            "category": question.category,
            "difficulty": question.difficulty,
            "question_type": question.question_type,
        },
        "adaptive_info": params,
    }


def _existing_question_response(question: Question, questions: list[Question], total_questions: int) -> dict:
    return _question_response(
        question,
        questions.index(question) + 1,
        total_questions,
        {
            "next_difficulty": question.difficulty,
            "next_question_type": question.question_type,
            "focus_area": question.category,
            "performance_trend": "stable",
            "difficulty_changed": False,
        },
    )


@router.post("/next-question")
async def next_question(
    body: AdaptiveNextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Idempotently retrieve the pending question or generate the next one."""
    try:
        session = db.query(InterviewSession).filter(
            InterviewSession.id == body.session_id,
            InterviewSession.user_id == current_user.id,
        ).with_for_update().first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        if session.status != "IN_PROGRESS":
            raise HTTPException(status_code=409, detail="Interview session is not in progress.")

        questions = db.query(Question).filter(
            Question.session_id == body.session_id
        ).order_by(Question.id).all()
        metadata = session.session_metadata or {}
        total_questions = metadata.get("question_count", 5)

        current_index = None
        if body.current_question_id is not None:
            current_index = next(
                (index for index, question in enumerate(questions)
                 if question.id == body.current_question_id),
                None,
            )
            if current_index is None:
                raise HTTPException(status_code=404, detail="Current question was not found in this interview.")
            current_answer = db.query(Answer.id).filter(
                Answer.question_id == body.current_question_id
            ).first()
            if not current_answer:
                return _existing_question_response(
                    questions[current_index],
                    questions,
                    total_questions,
                )

        pending_questions = questions[(current_index + 1) if current_index is not None else 0:]
        for question in pending_questions:
            if not db.query(Answer.id).filter(Answer.question_id == question.id).first():
                return _existing_question_response(question, questions, total_questions)

        if len(questions) >= total_questions:
            raise HTTPException(status_code=409, detail="All configured adaptive interview questions are complete.")

        answers = db.query(Answer).join(Question).filter(
            Question.session_id == body.session_id
        ).order_by(Answer.id).all()
        session_scores = [answer.score for answer in answers if answer.score is not None]
        memory = get_or_create(current_user.id, db)
        current_difficulty = questions[-1].difficulty if questions else (memory.last_difficulty or "MEDIUM")
        params = get_adaptive_params(
            session_scores=session_scores,
            current_difficulty=current_difficulty,
            interview_type=session.interview_type,
            weak_topics=memory.weak_topics or [],
        )

        asked = list(get_asked_questions(current_user.id, db))
        asked_normalized = {" ".join(item.casefold().split()) for item in asked}
        for question in questions:
            normalized = " ".join(question.question_text.casefold().split())
            if normalized not in asked_normalized:
                asked.append(question.question_text)
                asked_normalized.add(normalized)
        try:
            resume_context = retrieve_resume_context(current_user.id, body.category, k=2)
        except Exception as exc:
            logger.exception(
                "Adaptive resume context retrieval failed session_id=%s user_id=%s",
                body.session_id,
                current_user.id,
            )
            raise HTTPException(status_code=503, detail="Could not retrieve interview context. Please retry.") from exc

        question_text = generate_adaptive_question(
            category=body.category,
            difficulty=params["next_difficulty"],
            question_type=params["next_question_type"],
            asked_questions=asked,
            weak_topics=memory.weak_topics or [],
            strong_topics=memory.strong_topics or [],
            resume_context=resume_context or "",
            company=body.company,
        )
        if not isinstance(question_text, str) or not question_text.strip():
            raise HTTPException(status_code=502, detail="Groq returned an empty adaptive question.")

        question = Question(
            session_id=body.session_id,
            question_text=question_text.strip(),
            category=body.category,
            difficulty=params["next_difficulty"],
            question_type=params["next_question_type"],
        )
        db.add(question)
        memory.last_difficulty = params["next_difficulty"]
        session.total_questions = len(questions) + 1
        db.commit()
        db.refresh(question)
        record_question(current_user.id, question.question_text, db)

        return _question_response(question, len(questions) + 1, total_questions, params)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Adaptive question generation failed session_id=%s", body.session_id)
        raise HTTPException(status_code=502, detail="Adaptive question generation failed. Please retry.") from exc


@router.post("/submit-answer")
async def submit_answer(
    body: AdaptiveSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate an answer once, persist it, and update adaptive memory."""
    try:
        question = db.query(Question).filter(
            Question.id == body.question_id,
            Question.session_id == body.session_id,
        ).join(InterviewSession).filter(
            InterviewSession.user_id == current_user.id,
        ).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question was not found in this interview.")
        if not body.user_answer.strip():
            raise HTTPException(status_code=422, detail="Answer cannot be empty.")

        existing_answer = db.query(Answer).filter(
            Answer.question_id == body.question_id
        ).first()
        if existing_answer:
            if existing_answer.user_answer != body.user_answer:
                raise HTTPException(status_code=409, detail="An answer was already submitted for this question.")
            return _answer_response(existing_answer)

        from app.services.ai_service import ai_service

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
        return _answer_response(answer)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Adaptive answer evaluation failed session_id=%s question_id=%s", body.session_id, body.question_id)
        raise HTTPException(status_code=502, detail="Adaptive answer evaluation failed. Please retry.") from exc


def _answer_response(answer: Answer) -> dict:
    return {
        "answer_id": answer.id,
        "question_id": answer.question_id,
        "score": answer.score,
        "feedback": answer.ai_feedback,
        "ideal_answer": answer.ideal_answer,
        "strengths": answer.strengths,
        "improvements": answer.improvements,
        "evaluation": answer.evaluation_metadata or {},
    }
