"""Interview management service"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import (
    InterviewSession, Question, Answer, InterviewReport, Resume, JobDescription
)
from app.services.ai_service import ai_service
from app.services.company_rag_service import generate_company_questions


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
        is_followup: bool = False,
        parent_question_id: Optional[int] = None,
        db: Session = None,
    ) -> Question:
        """Generate and save a new question for a session"""
        
        question_type = "FOLLOW_UP" if is_followup else "TECHNICAL"

        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        metadata = session.session_metadata or {}
        company = metadata.get("company") if metadata else None

        if session and metadata.get("company_mode") and company:
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
            company_payload = generate_company_questions(
                company=company,
                role=metadata.get("role"),
                experience=metadata.get("experience"),
                skills=metadata.get("skills"),
                resume_text=latest_resume.resume_text if latest_resume else None,
                job_description=latest_jd.content if latest_jd else None,
                question_types=[category],
            )
            question_text = company_payload.get("questions", [{}])[0].get("question") or ai_service.generate_interview_question(
                category=category,
                difficulty=difficulty,
                question_type=question_type,
            )
        else:
            question_text = ai_service.generate_interview_question(
                category=category,
                difficulty=difficulty,
                question_type=question_type,
            )
        
        question = Question(
            session_id=session_id,
            question_text=question_text,
            category=category,
            difficulty=difficulty,
            question_type=question_type,
            parent_question_id=parent_question_id if is_followup else None,
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        return question
    
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
        
        # Evaluate answer using AI
        evaluation = ai_service.evaluate_answer(
            question=question.question_text,
            user_answer=user_answer,
            category=question.category,
            difficulty=question.difficulty,
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
        if answers:
            overall_score = sum(a.score for a in answers if a.score) / len(answers)
        else:
            overall_score = 0.0
        
        # Calculate duration
        duration_minutes = int(
            (datetime.utcnow() - session.started_at).total_seconds() / 60
        )
        
        session.status = "COMPLETED"
        session.completed_at = datetime.utcnow()
        session.overall_score = overall_score
        session.duration_minutes = duration_minutes
        session.total_questions = len(answers)
        
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
