"""
Career Coach service — skill gap, resume match, learning plans, hiring probability.
"""
import json
from typing import Dict, Optional
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat
from app.services.rag_service import retrieve_resume_context, retrieve_jd_context


def analyze_career(
    user_id: int,
    resume_text: str,
    jd_text: Optional[str],
    interview_score: Optional[float] = None,
    coding_score: Optional[float] = None,
    communication_score: Optional[float] = None,
) -> Dict:
    """Full career coach analysis."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    resume_ctx = retrieve_resume_context(user_id, "skills experience projects education") or resume_text[:2000]
    jd_ctx = retrieve_jd_context(user_id, "required skills responsibilities") or (jd_text or "")[:2000]

    perf_str = ""
    if interview_score is not None:
        perf_str += f"Interview Score: {interview_score}/10\n"
    if coding_score is not None:
        perf_str += f"Coding Score: {coding_score}/100\n"
    if communication_score is not None:
        perf_str += f"Communication Score: {communication_score}/10\n"

    prompt = f"""You are a Senior Career Coach with 20 years of experience in tech hiring.

CANDIDATE RESUME:
{resume_ctx}

JOB DESCRIPTION:
{jd_ctx or "Not provided — analyze resume standalone."}

PERFORMANCE DATA:
{perf_str or "No interview data yet."}

Perform a comprehensive career analysis. Return ONLY this JSON:
{{
    "resume_match_score": <0-100>,
    "job_match_score": <0-100>,
    "hiring_probability": <0-100>,
    "interview_readiness": <0-100>,
    "current_skills": ["<skill1>", "<skill2>"],
    "missing_skills": ["<skill1>", "<skill2>"],
    "skill_gap_analysis": {{
        "<skill>": {{"have": <0-10>, "required": <0-10>, "gap": "<description>"}}
    }},
    "recommended_courses": [
        {{"title": "<course>", "platform": "<Udemy/Coursera/etc>", "priority": "HIGH/MEDIUM/LOW"}}
    ],
    "recommended_certifications": ["<cert1>", "<cert2>"],
    "recommended_projects": [
        {{"title": "<project>", "description": "<what to build>", "skills_gained": ["<s1>"]}}
    ],
    "learning_plan_30": {{
        "goal": "<30-day goal>",
        "weeks": [
            {{"week": 1, "focus": "<topic>", "tasks": ["<task1>", "<task2>"]}}
        ]
    }},
    "learning_plan_60": {{
        "goal": "<60-day goal>",
        "weeks": [
            {{"week": 1, "focus": "<topic>", "tasks": ["<task1>"]}}
        ]
    }},
    "learning_plan_90": {{
        "goal": "<90-day goal>",
        "weeks": [
            {{"week": 1, "focus": "<topic>", "tasks": ["<task1>"]}}
        ]
    }},
    "resume_improvements": ["<improvement1>", "<improvement2>"],
    "interview_improvements": ["<tip1>", "<tip2>"],
    "ai_summary": "<3-4 sentence executive summary>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=3000)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {
            "resume_match_score": 60, "job_match_score": 55,
            "hiring_probability": 50, "interview_readiness": 55,
            "current_skills": [], "missing_skills": [],
            "skill_gap_analysis": {}, "recommended_courses": [],
            "recommended_certifications": [], "recommended_projects": [],
            "learning_plan_30": {}, "learning_plan_60": {}, "learning_plan_90": {},
            "resume_improvements": [], "interview_improvements": [],
            "ai_summary": "Analysis unavailable. Please try again.",
        }
