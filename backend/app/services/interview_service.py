"""Interview management service"""
from datetime import datetime
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import (
    InterviewSession, Question, Answer, InterviewReport, Resume, JobDescription
)
from app.services.ai_service import ai_service
from app.services.company_rag_service import generate_company_questions
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing interview sessions and questions"""
    
    @staticmethod
    def start_session(
        user_id: int,
        interview_type: str,
        category: Optional[str] = None,
        difficulty: str = "MEDIUM",
        db: Session = None,
        session_metadata: Optional[dict] = None,
    ) -> InterviewSession:
        """Start a new interview session"""
        
        session = InterviewSession(
            user_id=user_id,
            interview_type=interview_type,
            status="IN_PROGRESS",
            session_metadata=session_metadata or {},
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    def generate_question(
        session_id: int,
        category: str,
        difficulty: str = "MEDIUM",
        question_number: Optional[int] = None,
        is_followup: bool = False,
        parent_question_id: Optional[int] = None,
        db: Session = None,
    ) -> Question:
        """Generate and save a new question for a session"""
        
        question_type = "FOLLOW_UP" if is_followup else "TECHNICAL"

        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).with_for_update().first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        if session.status != "IN_PROGRESS":
            raise HTTPException(status_code=409, detail="Interview session is not in progress.")
        metadata = session.session_metadata or {}
        company = metadata.get("company") if metadata else None
        existing_questions = db.query(Question).filter(
            Question.session_id == session_id
        ).order_by(Question.id).all()
        target_number = question_number or len(existing_questions) + 1
        question_count = metadata.get("question_count", 5)
        if target_number < 1 or target_number > question_count:
            raise HTTPException(status_code=409, detail="Question number is outside this interview.")
        existing_target = None
        if target_number <= len(existing_questions):
            existing_target = existing_questions[target_number - 1]
            if isinstance(existing_target.question_text, str) and existing_target.question_text.strip():
                return InterviewService._attach_question_metadata(
                    existing_target,
                    target_number,
                    question_count,
                    metadata,
                )
        elif target_number != len(existing_questions) + 1:
            raise HTTPException(status_code=409, detail="Questions must be generated in order.")

        if session and metadata.get("company_mode") and company:
            category = metadata.get("interview_round") or metadata.get("category") or category
            difficulty = metadata.get("difficulty") or difficulty
            latest_resume = (
                db.query(Resume)
                .filter(Resume.user_id == session.user_id)
                .order_by(Resume.uploaded_at.desc())
                .first()
            )
            latest_jd = (
                db.query(JobDescription)
                .filter(JobDescription.user_id == session.user_id)
                .order_by(JobDescription.uploaded_at.desc())
                .first()
            )
            previous_questions = [
                item[0] for item in db.query(Question.question_text)
                .filter(Question.session_id == session_id).all()
            ]
            try:
                company_payload = generate_company_questions(
                    company=company,
                    role=metadata.get("role"),
                    experience=metadata.get("experience"),
                    skills=metadata.get("skills"),
                    resume_text=latest_resume.resume_text if latest_resume else None,
                    job_description=metadata.get("job_description")
                    or (latest_jd.content if latest_jd else None),
                    question_types=[category],
                    difficulty=metadata.get("difficulty", difficulty),
                    interview_round=metadata.get("interview_round"),
                    previous_questions=previous_questions,
                    question_number=target_number,
                    question_count=question_count,
                    interview_duration_minutes=metadata.get("interview_duration_minutes"),
                )
            except HTTPException:
                logger.exception("Company question generation provider failed for session %s", session_id)
                raise
            except Exception as exc:
                logger.exception("Company question generation failed for session %s", session_id)
                raise RuntimeError(
                    "Unable to generate a valid company interview question. Please try again."
                ) from exc
            try:
                question_data = company_payload["questions"][0]
                question_text = question_data["question"]
            except (KeyError, IndexError, TypeError) as exc:
                logger.exception("Company question generator returned an invalid response for session %s", session_id)
                raise HTTPException(
                    status_code=502,
                    detail="Question generation returned an invalid response. Please retry.",
                ) from exc
        else:
            question_text = ai_service.generate_interview_question(
                category=category,
                difficulty=difficulty,
                question_type=question_type,
            )
        if not isinstance(question_text, str) or not question_text.strip():
            raise HTTPException(
                status_code=502,
                detail="Question generation returned no question text. Please retry.",
            )

        question = existing_target or Question(session_id=session_id)
        question.question_text = question_text.strip()
        question.category = category
        question.difficulty = difficulty
        question.question_type = question_type
        question.parent_question_id = parent_question_id if is_followup else None
        if existing_target is None:
            db.add(question)
        db.commit()
        db.refresh(question)

        if session and metadata.get("company_mode") and company:
            updated_metadata = dict(metadata)
            details = dict(updated_metadata.get("question_details", {}))
            details[str(question.id)] = {
                "topic": question_data["topic"],
                "context": question_data["context"],
                "evaluation_criteria": question_data["evaluation_criteria"],
                "company_specific": question_data["company_specific"],
            }
            updated_metadata["question_details"] = details
            session.session_metadata = updated_metadata
            db.commit()
            db.refresh(session)

        return InterviewService._attach_question_metadata(
            question,
            target_number,
            question_count,
            session.session_metadata or {},
        )

    @staticmethod
    def _attach_question_metadata(question, question_number, question_count, metadata):
        if not isinstance(question.question_text, str) or not question.question_text.strip():
            raise HTTPException(
                status_code=502,
                detail="A saved interview question has no question text. Retry to regenerate it.",
            )
        question.question_number = question_number
        question.question_id = question.id
        question.total_questions = question_count
        details = (metadata.get("question_details") or {}).get(str(question.id), {})
        question.topic = details.get("topic")
        question.context = details.get("context")
        question.evaluation_criteria = details.get("evaluation_criteria")
        question.company_specific = details.get("company_specific")
        question.question = question.question_text
        question.is_answered = bool(question.answers)
        question.is_skipped = question.id in (metadata.get("skipped_question_ids") or [])
        question.status = "answered" if question.is_answered else "skipped" if question.is_skipped else "in_progress"
        return question

    @staticmethod
    def next_question(
        session_id: int,
        current_question_id: Optional[int],
        action: str,
        db: Session,
    ) -> Question:
        """Return the next persisted question or create exactly the next one."""
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).with_for_update().first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        if session.status != "IN_PROGRESS":
            raise HTTPException(status_code=409, detail="Interview session is not in progress.")

        questions = db.query(Question).filter(
            Question.session_id == session_id
        ).order_by(Question.id).all()
        metadata = session.session_metadata or {}
        skipped_ids = list(metadata.get("skipped_question_ids") or [])

        if current_question_id is None:
            if action != "start":
                raise HTTPException(status_code=422, detail="A current question is required.")
            next_number = next(
                (
                    index + 1 for index, question in enumerate(questions)
                    if not question.answers and question.id not in skipped_ids
                ),
                len(questions) + 1,
            )
        else:
            current_index = next(
                (index for index, question in enumerate(questions) if question.id == current_question_id),
                None,
            )
            if current_index is None:
                raise HTTPException(status_code=404, detail="Question not found in this interview.")
            current_question = questions[current_index]
            has_answer = db.query(Answer.id).filter(
                Answer.question_id == current_question.id
            ).first() is not None
            if action == "answered" and not has_answer:
                raise HTTPException(status_code=409, detail="Submit an answer before advancing.")
            if action == "skip":
                if has_answer:
                    raise HTTPException(status_code=409, detail="An answered question cannot be skipped.")
                if current_question.id not in skipped_ids:
                    skipped_ids.append(current_question.id)
                    updated_metadata = dict(metadata)
                    updated_metadata["skipped_question_ids"] = skipped_ids
                    session.session_metadata = updated_metadata
                    db.commit()
                    metadata = updated_metadata
            elif action != "answered":
                raise HTTPException(status_code=422, detail="Action must be 'answered' or 'skip'.")
            next_number = current_index + 2
            while next_number <= len(questions):
                next_question = questions[next_number - 1]
                if not next_question.answers and next_question.id not in skipped_ids:
                    break
                next_number += 1

        question_count = metadata.get("question_count", 5)
        if next_number > question_count:
            raise HTTPException(status_code=409, detail="There are no more questions in this interview.")
        if next_number <= len(questions):
            next_question = questions[next_number - 1]
            if not isinstance(next_question.question_text, str) or not next_question.question_text.strip():
                return InterviewService.generate_question(
                    session_id=session_id,
                    category=metadata.get("interview_round") or metadata.get("category") or next_question.category,
                    difficulty=metadata.get("difficulty") or next_question.difficulty,
                    question_number=next_number,
                    db=db,
                )
            return InterviewService._attach_question_metadata(next_question, next_number, question_count, metadata)

        category = metadata.get("interview_round") or metadata.get("category") or "Technical"
        difficulty = metadata.get("difficulty") or "MEDIUM"
        return InterviewService.generate_question(
            session_id=session_id,
            category=category,
            difficulty=difficulty,
            question_number=next_number,
            db=db,
        )

    @staticmethod
    def skip_question(session_id: int, question_id: int, db: Session) -> None:
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        if session.status != "IN_PROGRESS":
            raise HTTPException(status_code=409, detail="Interview session is not in progress.")
        question = db.query(Question).filter(
            Question.id == question_id,
            Question.session_id == session_id,
        ).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found in this interview.")
        if db.query(Answer.id).filter(Answer.question_id == question_id).first():
            raise HTTPException(status_code=409, detail="An answered question cannot be skipped.")
        metadata = dict(session.session_metadata or {})
        skipped_ids = list(metadata.get("skipped_question_ids") or [])
        if question_id not in skipped_ids:
            skipped_ids.append(question_id)
            metadata["skipped_question_ids"] = skipped_ids
            session.session_metadata = metadata
            db.commit()
    
    @staticmethod
    def submit_answer(
        question_id: int,
        user_answer: str,
        db: Session = None,
    ) -> Answer:
        """Submit and evaluate user answer"""
        
        # Get question details
        question = db.query(Question).filter(
            Question.id == question_id
        ).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found.")
        if not user_answer or not user_answer.strip():
            raise HTTPException(status_code=422, detail="Answer cannot be empty.")
        existing_answer = db.query(Answer).filter(
            Answer.question_id == question_id
        ).first()
        if existing_answer:
            if existing_answer.user_answer != user_answer:
                raise HTTPException(
                    status_code=409,
                    detail="An answer has already been submitted for this question.",
                )
            return existing_answer
        
        # Evaluate answer using AI
        evaluation = ai_service.evaluate_answer(
            question=question.question_text,
            user_answer=user_answer,
            category=question.category,
            difficulty=question.difficulty,
            evaluation_criteria=(
                (question.session.session_metadata or {}).get("question_details", {})
                .get(str(question.id), {}).get("evaluation_criteria")
            ),
        )
        
        # Create answer record
        answer = Answer(
            question_id=question_id,
            user_answer=user_answer,
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
        
        return answer
    
    @staticmethod
    def end_session(session_id: int, db: Session = None) -> InterviewSession:
        """End interview session and calculate overall score"""
        
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()
        
        # Get all answers for this session
        answers = db.query(Answer).join(Question).filter(
            Question.session_id == session_id
        ).all()
        
        # Calculate overall score
        scored_answers = [a.score for a in answers if a.score is not None]
        overall_score = sum(scored_answers) / len(scored_answers) if scored_answers else None
        
        # Calculate duration
        duration_minutes = int(
            (datetime.utcnow() - session.started_at).total_seconds() / 60
        )
        
        session.status = "COMPLETED"
        session.completed_at = datetime.utcnow()
        session.overall_score = overall_score
        session.duration_minutes = duration_minutes
        session.total_questions = db.query(Question).filter(
            Question.session_id == session_id
        ).count()
        
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    def generate_report(session_id: int, db: Session = None) -> InterviewReport:
        """Generate comprehensive report for interview session"""
        
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()
        
        answers = db.query(Answer).join(Question).filter(
            Question.session_id == session_id
        ).all()
        
        # Prepare data for performance analysis
        answers_data = [
            {
                "question": db.query(Question).filter(
                    Question.id == a.question_id
                ).first().question_text,
                "answer": a.user_answer,
                "score": a.score,
            }
            for a in answers
        ]
        
        # Get AI analysis
        performance_analysis = ai_service.analyze_performance(
            answers_data=answers_data,
            interview_type=session.interview_type,
        )
        
        # Calculate metrics
        technical_scores = [a.technical_accuracy for a in answers if a.technical_accuracy]
        communication_scores = [a.communication_score for a in answers if a.communication_score]
        
        report = InterviewReport(
            session_id=session_id,
            user_id=session.user_id,
            overall_score=session.overall_score or 0.0,
            technical_score=sum(technical_scores) / len(technical_scores) if technical_scores else None,
            communication_score=sum(communication_scores) / len(communication_scores) if communication_scores else None,
            summary=performance_analysis.get("overall_assessment"),
            strengths_list=performance_analysis.get("strengths"),
            improvements_list=performance_analysis.get("weaknesses"),
            recommendations=performance_analysis.get("next_steps"),
            performance_metrics=performance_analysis,
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report


from typing import Optional
