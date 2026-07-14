"""AI service for integrating with Groq API"""
import json
from typing import Optional, List
from groq import Groq, AuthenticationError, APIConnectionError
from fastapi import HTTPException
from app.config import settings


def _chat(client: Groq, model: str, prompt: str, max_tokens: int = 1000) -> str:
    """Helper: single-turn chat completion via Groq"""
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Groq API key is invalid or missing. Set GROQ_API_KEY in backend/.env and restart the server."
        )
    except APIConnectionError:
        raise HTTPException(
            status_code=500,
            detail="Cannot reach Groq API. Check your internet connection."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


class AIService:
    """Service for AI-powered interview features"""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate_interview_question(
        self,
        category: str,
        difficulty: str = "MEDIUM",
        question_type: str = "TECHNICAL",
        previous_topics: Optional[List[str]] = None,
    ) -> str:
        prompt = f"""You are an expert interview coach.

Generate a single {difficulty} difficulty {question_type} interview question for the {category} category.

Requirements:
- Make it specific and practical
- Include a real-world scenario when relevant
- Be concise (2-3 sentences max)
- Previous topics covered: {", ".join(previous_topics) if previous_topics else "None"}

Return ONLY the question text, no numbering or explanation."""

        return _chat(self.client, self.model, prompt, max_tokens=300)

    def generate_followup_question(
        self,
        original_question: str,
        user_answer: str,
        category: str,
    ) -> str:
        prompt = f"""You are an expert interviewer.

Original Question: {original_question}
Candidate's Answer: {user_answer}
Category: {category}

Generate a single follow-up question (1-2 sentences) that digs deeper into a gap or edge case in the candidate's answer.

Return ONLY the follow-up question."""

        return _chat(self.client, self.model, prompt, max_tokens=200)

    def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        category: str,
        difficulty: str = "MEDIUM",
    ) -> dict:
        prompt = f"""You are an expert technical interviewer.

Question: {question}
Candidate's Answer: {user_answer}
Category: {category}
Difficulty: {difficulty}

Evaluate on: Technical Accuracy (0-10), Completeness (0-10), Clarity (0-10), Communication (0-10).

Return ONLY this JSON (no extra text):
{{
    "score": <overall 0-10>,
    "technical_accuracy": <0-10>,
    "completeness": <0-10>,
    "clarity": <0-10>,
    "communication_score": <0-10>,
    "feedback": "<2-3 sentences of constructive feedback>",
    "strengths": "<1-2 key strengths>",
    "improvements": "<1-2 areas for improvement>",
    "ideal_answer": "<concise model answer, 3-5 sentences>"
}}"""

        text = _chat(self.client, self.model, prompt, max_tokens=1000)
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            return {
                "score": 5.0,
                "technical_accuracy": 5.0,
                "completeness": 5.0,
                "clarity": 5.0,
                "communication_score": 5.0,
                "feedback": "Unable to fully evaluate response.",
                "strengths": "Answer attempted the question.",
                "improvements": "More detail and examples would strengthen the answer.",
                "ideal_answer": "Please refer to learning materials for a complete answer.",
            }

    def analyze_performance(self, answers_data: List[dict], interview_type: str) -> dict:
        summary = "\n".join(
            f"Q: {item['question']}\nA: {item['answer']}\nScore: {item['score']}\n"
            for item in answers_data
        )

        prompt = f"""You are a professional interview coach.

Interview Type: {interview_type}
Answers and Scores:
{summary}

Return ONLY this JSON:
{{
    "overall_assessment": "<2-3 sentence assessment>",
    "strengths": ["<s1>", "<s2>", "<s3>"],
    "weaknesses": ["<w1>", "<w2>", "<w3>"],
    "improvement_areas": {{"<area>": "<suggestion>"}},
    "next_steps": ["<step1>", "<step2>", "<step3>"],
    "recommended_topics": ["<t1>", "<t2>", "<t3>"]
}}"""

        text = _chat(self.client, self.model, prompt, max_tokens=1500)
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            return {
                "overall_assessment": "Good effort overall.",
                "strengths": ["Communication", "Technical foundation"],
                "weaknesses": ["Depth of knowledge", "Time management"],
                "improvement_areas": {},
                "next_steps": ["Review core concepts", "Practice more problems"],
                "recommended_topics": ["System Design", "Advanced Algorithms"],
            }


ai_service = AIService()
