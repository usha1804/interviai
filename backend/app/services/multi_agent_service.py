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
import logging
from typing import List, Dict, Optional
from fastapi import HTTPException
from app.config import settings
from app.services.ai_service import _chat, get_groq_client
from app.services.report_prompt_utils import estimate_prompt_tokens

logger = logging.getLogger(__name__)

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
        return _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=300)


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
        text = _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=600)
        try:
            s, e = text.find("{"), text.rfind("}") + 1
            if s < 0 or e <= s:
                raise ValueError("Evaluation response did not contain JSON.")
            evaluation = json.loads(text[s:e])
            if not isinstance(evaluation, dict):
                raise ValueError("Evaluation response must be a JSON object.")
            for field in ("score", "technical_accuracy", "completeness", "clarity", "communication_score"):
                if not isinstance(evaluation.get(field), (int, float)) or not 0 <= evaluation[field] <= 10:
                    raise ValueError(f"Evaluation response has an invalid {field}.")
            return evaluation
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="AI evaluation failed. Please retry.") from exc


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
        text = _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=1200)
        try:
            s, e = text.find("{"), text.rfind("}") + 1
            if s < 0 or e <= s:
                raise ValueError("Feedback response did not contain JSON.")
            feedback = json.loads(text[s:e])
            if not isinstance(feedback, dict) or not isinstance(feedback.get("detailed_feedback"), str):
                raise ValueError("Feedback response is incomplete.")
            return feedback
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="AI feedback generation failed. Please retry.") from exc


# ── Agent 4: Performance Analyzer ────────────────────────────────

class PerformanceAgent:
    """Analyzes full interview, generates skill matrix and hiring recommendation."""

    def build_prompt(
        self,
        answers_data: List[Dict],
        interview_type: str,
        resume_context: str,
        jd_context: str,
    ) -> str:
        report_input = {
            "interview_type": interview_type,
            "resume_context": resume_context,
            "job_description_context": jd_context,
            "responses": answers_data,
        }
        return """Analyze the interview data and return only one JSON object. Use the existing per-answer scores as evidence and do not invent facts.
Required fields: overall_score, technical_score, communication_score, hiring_probability (0-100);
hiring_recommendation (STRONG_YES|YES|MAYBE|NO); skill_matrix (object of 0-100 scores);
radar_chart_data (array of {subject,score}); strengths, weaknesses, topics_to_improve,
learning_recommendations (arrays of strings); ai_summary (string); interview_readiness (0-100).
Interview data:
""" + json.dumps(report_input, ensure_ascii=False, separators=(",", ":"))

    def run(
        self,
        answers_data: List[Dict],
        interview_type: str,
        resume_context: str,
        jd_context: str,
    ) -> Dict:
        prompt = self.build_prompt(answers_data, interview_type, resume_context, jd_context)
        logger.info(
            "Report analysis prompt estimated_input_tokens=%s response_entries=%s",
            estimate_prompt_tokens(prompt, settings.GROQ_MODEL),
            len(answers_data),
        )
        text = _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=2000)
        try:
            s, e = text.find("{"), text.rfind("}") + 1
            if s < 0 or e <= s:
                raise ValueError("Performance analysis response did not contain JSON.")
            analysis = json.loads(text[s:e])
            if not isinstance(analysis, dict):
                raise ValueError("Performance analysis response must be a JSON object.")
            for field in ("overall_score", "technical_score", "communication_score", "hiring_probability"):
                if not isinstance(analysis.get(field), (int, float)) or not 0 <= analysis[field] <= 100:
                    raise ValueError(f"Performance analysis response has an invalid {field}.")
            if not isinstance(analysis.get("ai_summary"), str):
                raise ValueError("Performance analysis response is missing its summary.")
            if analysis.get("hiring_recommendation") not in {"STRONG_YES", "YES", "MAYBE", "NO"}:
                raise ValueError("Performance analysis response has an invalid recommendation.")
            if not isinstance(analysis.get("skill_matrix"), dict):
                raise ValueError("Performance analysis response has an invalid skill matrix.")
            for field in (
                "radar_chart_data", "strengths", "weaknesses",
                "topics_to_improve", "learning_recommendations",
            ):
                if not isinstance(analysis.get(field), list):
                    raise ValueError(f"Performance analysis response has invalid {field}.")
            return analysis
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="AI report generation failed. Please retry.") from exc


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
