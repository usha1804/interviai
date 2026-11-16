"""
Adaptive Interview Engine
Dynamically adjusts question difficulty and type based on candidate performance.
Uses interview memory + running score to decide next question parameters.
"""
import json
from typing import List, Dict, Optional, Tuple
from fastapi import HTTPException
from app.config import settings
from app.services.ai_service import _chat, get_groq_client

DIFFICULTY_LADDER = ["EASY", "MEDIUM", "HARD", "SYSTEM_DESIGN", "LEADERSHIP"]
DIFFICULTY_UP_THRESHOLD = 7.0    # score >= this → increase difficulty
DIFFICULTY_DOWN_THRESHOLD = 4.0  # score < this  → decrease difficulty


def compute_next_difficulty(scores: List[float], current: str) -> str:
    """Given last 3 scores and current difficulty, return next difficulty."""
    if not scores:
        return current
    recent = scores[-3:]
    avg = sum(recent) / len(recent)
    idx = DIFFICULTY_LADDER.index(current) if current in DIFFICULTY_LADDER else 1

    if avg >= DIFFICULTY_UP_THRESHOLD and idx < len(DIFFICULTY_LADDER) - 1:
        return DIFFICULTY_LADDER[idx + 1]
    if avg < DIFFICULTY_DOWN_THRESHOLD and idx > 0:
        return DIFFICULTY_LADDER[idx - 1]
    return current


def compute_next_question_type(scores: List[float], interview_type: str) -> str:
    """Decide question type based on performance pattern."""
    if not scores:
        return "TECHNICAL" if interview_type != "HR" else "BEHAVIORAL"
    avg = sum(scores[-3:]) / len(scores[-3:])
    if interview_type == "HR":
        return "BEHAVIORAL"
    if avg >= 8.0:
        return "SYSTEM_DESIGN"
    if avg >= 6.0:
        return "TECHNICAL"
    return "CONCEPTUAL"


def generate_adaptive_question(
    category: str,
    difficulty: str,
    question_type: str,
    asked_questions: List[str],
    weak_topics: List[str],
    strong_topics: List[str],
    resume_context: str = "",
    company: Optional[str] = None,
) -> str:
    """Generate the next adaptive question using AI."""
    asked_str = "\n".join(f"- {q}" for q in asked_questions[-10:]) or "None"
    weak_str = ", ".join(weak_topics[:5]) or "None identified yet"
    strong_str = ", ".join(strong_topics[:5]) or "None identified yet"
    company_line = f"Company: {company}. Align with their interview style.\n" if company else ""

    prompt = f"""You are an adaptive AI interviewer.
{company_line}
Category: {category}
Current Difficulty: {difficulty}
Question Type: {question_type}
Candidate Weak Topics: {weak_str}
Candidate Strong Topics: {strong_str}
Resume Context: {resume_context[:500] or "N/A"}

Already Asked (do NOT repeat):
{asked_str}

Rules:
- If difficulty is SYSTEM_DESIGN: ask architecture/scaling questions
- If difficulty is LEADERSHIP: ask leadership/conflict/strategy questions
- Focus on weak topics to help candidate improve
- Be specific, practical, and progressively challenging

Generate ONE adaptive interview question. Return ONLY the question text."""

    response_text = _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=300).strip()
    if len(response_text) < 10:
        raise HTTPException(status_code=502, detail="Groq returned an unusable adaptive interview question.")
    asked_normalized = {" ".join(item.casefold().split()) for item in asked_questions}
    if " ".join(response_text.casefold().split()) in asked_normalized:
        raise HTTPException(status_code=502, detail="Groq repeated a previous question. Retry to generate a different one.")
    return response_text


def get_adaptive_params(
    session_scores: List[float],
    current_difficulty: str,
    interview_type: str,
    weak_topics: List[str],
) -> Dict:
    """Return next difficulty, question type, and focus area."""
    next_diff = compute_next_difficulty(session_scores, current_difficulty)
    next_type = compute_next_question_type(session_scores, interview_type)
    focus = weak_topics[0] if weak_topics else "General"
    trend = "improving" if len(session_scores) >= 2 and session_scores[-1] > session_scores[-2] else "stable"

    return {
        "next_difficulty": next_diff,
        "next_question_type": next_type,
        "focus_area": focus,
        "performance_trend": trend,
        "difficulty_changed": next_diff != current_difficulty,
    }
