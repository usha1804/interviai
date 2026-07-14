"""
Multi-Agent AI System
─────────────────────
Agent 1 — QuestionAgent    : generates questions from resume + JD context
Agent 2 — EvaluatorAgent   : scores answers across multiple dimensions
Agent 3 — FeedbackAgent    : produces detailed feedback + learning resources
Agent 4 — PerformanceAgent : full interview analysis, skill matrix, hiring recommendation
Coordinator                : orchestrates the pipeline
"""
import json
from typing import List, Dict, Optional
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat


def _client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


# ── Agent 1: Question Generator ───────────────────────────────────

class QuestionAgent:
    """Generates targeted interview questions from resume + JD context."""

    def run(
        self,
        resume_context: str,
        jd_context: str,
        question_type: str,
        difficulty: str,
        asked_questions: List[str],
        company: Optional[str] = None,
    ) -> str:
        asked_str = "\n".join(f"- {q}" for q in asked_questions[-15:]) or "None"
        company_line = f"Company style: {company}. " if company else ""
        prompt = f"""You are an expert interviewer. {company_line}

Resume Context: {resume_context or "N/A"}
Job Description Context: {jd_context or "N/A"}
Question Type: {question_type}
Difficulty: {difficulty}
Already Asked (do NOT repeat):
{asked_str}

Generate ONE specific, insightful {question_type} interview question grounded in the context above.
Return ONLY the question text."""
        return _chat(_client(), settings.GROQ_MODEL, prompt, max_tokens=300)


# ── Agent 2: Answer Evaluator ─────────────────────────────────────

class EvaluatorAgent:
    """Scores a candidate's answer across 5 dimensions."""

    def run(
        self,
        question: str,
        answer: str,
        category: str,
        resume_context: str,
        jd_context: str,
    ) -> Dict:
        prompt = f"""You are a strict technical interviewer evaluating a candidate.

Resume Context: {resume_context or "N/A"}
JD Context: {jd_context or "N/A"}
Question: {question}
Candidate Answer: {answer}
Category: {category}

Score each dimension 0-10. Return ONLY this JSON:
{{
    "score": <overall 0-10>,
    "technical_accuracy": <0-10>,
    "completeness": <0-10>,
    "clarity": <0-10>,
    "communication_score": <0-10>,
    "resume_alignment": <0-10>,
    "raw_feedback": "<one sentence>"
}}"""
        text = _chat(_client(), settings.GROQ_MODEL, prompt, max_tokens=600)
        try:
            s, e = text.find("{"), text.rfind("}") + 1
            return json.loads(text[s:e])
        except Exception:
            return {
                "score": 5.0, "technical_accuracy": 5.0, "completeness": 5.0,
                "clarity": 5.0, "communication_score": 5.0, "resume_alignment": 5.0,
                "raw_feedback": "Evaluation unavailable.",
            }


# ── Agent 3: Feedback Generator ───────────────────────────────────

class FeedbackAgent:
    """Generates detailed feedback with learning resources."""

    def run(self, question: str, answer: str, scores: Dict, category: str) -> Dict:
        prompt = f"""You are a senior career coach providing interview feedback.

Question: {question}
Answer: {answer}
Scores: {json.dumps(scores)}
Category: {category}

Return ONLY this JSON:
{{
    "strengths": ["<s1>", "<s2>"],
    "weaknesses": ["<w1>", "<w2>"],
    "improvement_suggestions": ["<i1>", "<i2>", "<i3>"],
    "learning_resources": [
        {{"title": "<resource>", "type": "Course/Book/Doc", "url": "<url or search term>"}}
    ],
    "ideal_answer": "<model answer 3-5 sentences>",
    "detailed_feedback": "<2-3 paragraph coaching feedback>"
}}"""
        text = _chat(_client(), settings.GROQ_MODEL, prompt, max_tokens=1200)
        try:
            s, e = text.find("{"), text.rfind("}") + 1
            return json.loads(text[s:e])
        except Exception:
            return {
                "strengths": ["Attempted the question"],
                "weaknesses": ["Needs more depth"],
                "improvement_suggestions": ["Study core concepts", "Practice with examples"],
                "learning_resources": [],
                "ideal_answer": "N/A",
                "detailed_feedback": "Please review the topic and try again.",
            }


# ── Agent 4: Performance Analyzer ────────────────────────────────

class PerformanceAgent:
    """Analyzes full interview, generates skill matrix and hiring recommendation."""

    def run(
        self,
        answers_data: List[Dict],
        interview_type: str,
        resume_context: str,
        jd_context: str,
    ) -> Dict:
        summary = "\n".join(
            f"Q{i+1}: {d['question']}\nA: {d['answer']}\nScore: {d['score']}/10"
            for i, d in enumerate(answers_data)
        )
        prompt = f"""You are a hiring manager analyzing a complete interview.

Interview Type: {interview_type}
Resume Context: {resume_context or "N/A"}
JD Context: {jd_context or "N/A"}

Interview Transcript:
{summary}

Return ONLY this JSON:
{{
    "overall_score": <0-100>,
    "technical_score": <0-100>,
    "communication_score": <0-100>,
    "confidence_score": <0-100>,
    "hiring_probability": <0-100>,
    "hiring_recommendation": "<STRONG_YES|YES|MAYBE|NO>",
    "skill_matrix": {{"<skill>": <0-100>}},
    "radar_chart_data": [{{"subject": "<dim>", "score": <0-100>}}],
    "strengths": ["<s1>", "<s2>", "<s3>"],
    "weaknesses": ["<w1>", "<w2>", "<w3>"],
    "topics_to_improve": ["<t1>", "<t2>", "<t3>"],
    "learning_recommendations": ["<r1>", "<r2>", "<r3>"],
    "ai_summary": "<3-4 sentence executive summary>",
    "interview_readiness": <0-100>
}}"""
        text = _chat(_client(), settings.GROQ_MODEL, prompt, max_tokens=2000)
        try:
            s, e = text.find("{"), text.rfind("}") + 1
            return json.loads(text[s:e])
        except Exception:
            return {
                "overall_score": 60, "technical_score": 60, "communication_score": 60,
                "confidence_score": 60, "hiring_probability": 50,
                "hiring_recommendation": "MAYBE",
                "skill_matrix": {}, "radar_chart_data": [],
                "strengths": [], "weaknesses": [], "topics_to_improve": [],
                "learning_recommendations": [],
                "ai_summary": "Analysis unavailable.", "interview_readiness": 50,
            }


# ── Coordinator ───────────────────────────────────────────────────

class AgentCoordinator:
    """Orchestrates all agents for a complete interview pipeline."""

    def __init__(self):
        self.question_agent = QuestionAgent()
        self.evaluator_agent = EvaluatorAgent()
        self.feedback_agent = FeedbackAgent()
        self.performance_agent = PerformanceAgent()

    def generate_question(
        self,
        resume_ctx: str,
        jd_ctx: str,
        question_type: str,
        difficulty: str,
        asked: List[str],
        company: Optional[str] = None,
    ) -> str:
        return self.question_agent.run(resume_ctx, jd_ctx, question_type, difficulty, asked, company)

    def evaluate_and_feedback(
        self,
        question: str,
        answer: str,
        category: str,
        resume_ctx: str,
        jd_ctx: str,
    ) -> Dict:
        scores = self.evaluator_agent.run(question, answer, category, resume_ctx, jd_ctx)
        feedback = self.feedback_agent.run(question, answer, scores, category)
        return {**scores, **feedback}

    def analyze_full_interview(
        self,
        answers_data: List[Dict],
        interview_type: str,
        resume_ctx: str,
        jd_ctx: str,
    ) -> Dict:
        return self.performance_agent.run(answers_data, interview_type, resume_ctx, jd_ctx)


coordinator = AgentCoordinator()
