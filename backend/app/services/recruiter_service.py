"""
Recruiter Service
Provides recruiter-facing data: candidate list, profiles, scores, hiring decisions.
"""
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat
from app.models.models import (
    User, InterviewSession, Answer, Question,
    CodingSession, ATSReport, GitHubAnalysis,
    EnhancedInterviewReport, RecruiterNote,
)


def get_all_candidates(db: Session, search: str = "", skip: int = 0, limit: int = 50) -> List[Dict]:
    """Return list of all USER-role candidates with summary stats."""
    query = db.query(User).filter(User.role == "USER", User.is_active == True)
    if search:
        query = query.filter(User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    users = query.offset(skip).limit(limit).all()

    result = []
    for u in users:
        sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == u.id,
            InterviewSession.status == "COMPLETED",
        ).all()
        scores = [s.overall_score for s in sessions if s.overall_score]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        ats = db.query(ATSReport).filter(ATSReport.user_id == u.id).order_by(ATSReport.created_at.desc()).first()
        gh = db.query(GitHubAnalysis).filter(GitHubAnalysis.user_id == u.id).order_by(GitHubAnalysis.analyzed_at.desc()).first()
        report = db.query(EnhancedInterviewReport).filter(EnhancedInterviewReport.user_id == u.id).order_by(EnhancedInterviewReport.created_at.desc()).first()

        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "total_interviews": len(sessions),
            "average_score": avg_score,
            "ats_score": ats.ats_score if ats else None,
            "github_score": gh.github_score if gh else None,
            "hiring_probability": report.hiring_probability if report else None,
            "hiring_recommendation": report.hiring_recommendation if report else None,
            "created_at": u.created_at.isoformat(),
        })
    return result


def get_candidate_profile(candidate_id: int, db: Session) -> Dict:
    """Full candidate profile for recruiter view."""
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        return {}

    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == candidate_id
    ).order_by(InterviewSession.started_at.desc()).all()

    coding = db.query(CodingSession).filter(
        CodingSession.user_id == candidate_id
    ).order_by(CodingSession.created_at.desc()).limit(5).all()

    ats = db.query(ATSReport).filter(ATSReport.user_id == candidate_id).order_by(ATSReport.created_at.desc()).first()
    gh = db.query(GitHubAnalysis).filter(GitHubAnalysis.user_id == candidate_id).order_by(GitHubAnalysis.analyzed_at.desc()).first()
    report = db.query(EnhancedInterviewReport).filter(EnhancedInterviewReport.user_id == candidate_id).order_by(EnhancedInterviewReport.created_at.desc()).first()

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at.isoformat()},
        "interview_sessions": [
            {
                "id": s.id, "type": s.interview_type, "score": s.overall_score,
                "status": s.status, "date": s.started_at.isoformat(),
                "duration": s.duration_minutes,
            }
            for s in sessions
        ],
        "coding_sessions": [
            {"id": c.id, "score": c.score, "language": c.language, "difficulty": c.difficulty}
            for c in coding
        ],
        "ats_report": {
            "ats_score": ats.ats_score, "keyword_match_pct": ats.keyword_match_pct,
            "matching_skills": ats.matching_skills, "missing_skills": ats.missing_skills,
        } if ats else None,
        "github": {
            "github_score": gh.github_score, "languages": gh.languages,
            "total_stars": gh.total_stars, "github_url": gh.github_url,
        } if gh else None,
        "enhanced_report": {
            "overall_score": report.overall_score,
            "technical_score": report.technical_score,
            "communication_score": report.communication_score,
            "hiring_probability": report.hiring_probability,
            "hiring_recommendation": report.hiring_recommendation,
            "strengths": report.strengths,
            "weaknesses": report.weaknesses,
            "ai_summary": report.ai_summary,
        } if report else None,
    }


def generate_hiring_decision(candidate_id: int, db: Session) -> Dict:
    """AI-generated hiring decision based on all available data."""
    profile = get_candidate_profile(candidate_id, db)
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""You are a Senior Hiring Manager making a hiring decision.

Candidate Data:
{json.dumps(profile, indent=2, default=str)[:3000]}

Based on all available data, generate a hiring decision.
Return ONLY this JSON:
{{
    "decision": "<STRONG_HIRE|HIRE|MAYBE|NO_HIRE>",
    "confidence": <0-100>,
    "key_strengths": ["<s1>", "<s2>"],
    "key_concerns": ["<c1>", "<c2>"],
    "recommendation": "<2-3 sentence hiring recommendation>",
    "suggested_role_level": "<Junior|Mid|Senior|Lead>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=800)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {
            "decision": "MAYBE", "confidence": 50,
            "key_strengths": [], "key_concerns": [],
            "recommendation": "Insufficient data for a confident decision.",
            "suggested_role_level": "Mid",
        }
