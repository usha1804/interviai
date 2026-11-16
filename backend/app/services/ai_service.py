"""AI service for integrating with Groq API"""
import json
import logging
import time
from functools import lru_cache
from typing import Optional, List
import httpx
from fastapi import HTTPException
from groq import Groq
from app.config import settings
from app.services.report_prompt_utils import estimate_prompt_tokens, request_payload_size

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    """Return the process-wide Groq client initialized from environment settings."""
    api_key = settings.GROQ_API_KEY
    if not isinstance(api_key, str) or not api_key.strip():
        raise HTTPException(
            status_code=503,
            detail="AI generation is unavailable: GROQ_API_KEY is not configured.",
        )
    try:
        return Groq(
            api_key=api_key,
            http_client=httpx.Client(timeout=30.0),
        )
    except Exception as exc:
        logger.exception("Could not initialize the Groq client")
        raise HTTPException(
            status_code=503,
            detail="Groq client initialization failed. Check the server AI configuration.",
        ) from exc


def _chat(client: Groq, model: str, prompt: str, max_tokens: int = 1000) -> str:
    """Run a single-turn Groq completion with a validated initialized client."""
    if not callable(getattr(getattr(getattr(client, "chat", None), "completions", None), "create", None)):
        raise HTTPException(
            status_code=500,
            detail="Invalid Groq client. Pass an initialized Groq client to the AI service.",
        )
    if not isinstance(model, str) or not model.strip():
        raise HTTPException(
            status_code=503,
            detail="AI generation is unavailable: GROQ_MODEL is not configured.",
        )
    logger.info(
        "Groq request model=%s messages=1 estimated_input_tokens=%s payload_bytes=%s",
        model,
        estimate_prompt_tokens(prompt, model),
        request_payload_size(model, prompt, max_tokens),
    )
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            choices = getattr(response, "choices", None) or []
            message = getattr(choices[0], "message", None) if choices else None
            content = getattr(message, "content", None)
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and isinstance(item.get("text"), str)
                )
            if not isinstance(content, str) or not content.strip():
                raise HTTPException(status_code=502, detail="Groq returned an empty response.")
            return content.strip()
        except HTTPException:
            raise
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            exception_name = type(exc).__name__.casefold()
            transient = status_code == 429 or (isinstance(status_code, int) and status_code >= 500)
            if transient and attempt < 2:
                delay = min(0.5 * (2 ** attempt), 2.0)
                logger.warning(
                    "Groq temporary failure status=%s model=%s; retrying after %.1f seconds",
                    status_code,
                    model,
                    delay,
                )
                time.sleep(delay)
                continue
            logger.warning(
                "Groq request failed model=%s status=%s error_type=%s",
                model,
                status_code,
                type(exc).__name__,
            )
            if status_code == 429:
                raise HTTPException(status_code=429, detail="Groq rate limit reached after retries. Please try again later.") from exc
            if status_code in (401, 403):
                raise HTTPException(status_code=502, detail="Groq authentication or permission check failed.") from exc
            if status_code == 413:
                raise HTTPException(status_code=413, detail="Groq rejected an oversized request.") from exc
            if status_code is not None and status_code >= 500:
                raise HTTPException(status_code=502, detail=f"Groq remained unavailable (HTTP {status_code}) after retries.") from exc
            if "timeout" in exception_name:
                raise HTTPException(status_code=504, detail="Groq request timed out. Please retry.") from exc
            if "connection" in exception_name or "network" in exception_name:
                raise HTTPException(status_code=503, detail="Could not connect to Groq. Please retry.") from exc
            if status_code == 400 or status_code == 404:
                raise HTTPException(
                    status_code=502,
                    detail=f"Groq rejected the model or request configuration (HTTP {status_code}).",
                ) from exc
            raise HTTPException(status_code=502, detail="Groq request failed. Please retry.") from exc


class AIService:
    """Service for AI-powered interview features"""

    def __init__(self):
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

        last_error = None
        for attempt in range(2):
            try:
                text = _chat(get_groq_client(), self.model, prompt, max_tokens=300)
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1]
                    if cleaned.rstrip().endswith("```"):
                        cleaned = cleaned.rstrip()[:-3].strip()
                if cleaned.startswith("{"):
                    start, end = cleaned.find("{"), cleaned.rfind("}") + 1
                    if end <= start:
                        raise ValueError("The model returned malformed JSON.")
                    payload = json.loads(cleaned[start:end])
                    cleaned = payload.get("question") or payload.get("question_text") or ""
                if not isinstance(cleaned, str) or len(cleaned.strip()) < 10:
                    raise ValueError("The model returned empty or unusable question text.")
                return cleaned.strip()
            except HTTPException as exc:
                last_error = exc
                if (
                    attempt == 1
                    or exc.status_code in (401, 403, 429)
                    or "API key" in str(exc.detail)
                    or "model not found" in str(exc.detail).lower()
                    or "not configured" in str(exc.detail)
                ):
                    raise
                logger.warning(
                    "Question generation attempt %s failed with HTTP %s; retrying",
                    attempt + 1,
                    exc.status_code,
                )
            except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as exc:
                last_error = exc
                logger.warning("Question generation attempt %s returned invalid content; retrying", attempt + 1)

        raise HTTPException(
            status_code=502,
            detail="Groq could not generate valid question text after two attempts. Please retry.",
        ) from last_error

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

        return _chat(get_groq_client(), self.model, prompt, max_tokens=200)

    def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        category: str,
        difficulty: str = "MEDIUM",
        evaluation_criteria: Optional[List[str]] = None,
    ) -> dict:
        prompt = f"""You are an expert technical interviewer.

Question: {question}
Candidate's Answer: {user_answer}
Category: {category}
Difficulty: {difficulty}
Evaluation criteria: {json.dumps(evaluation_criteria or [])}

Evaluate technical correctness, depth, relevance, problem-solving, clarity, and communication.
Use the evaluation criteria when provided. Score Technical Accuracy, Completeness, Clarity,
Communication, and the overall answer from 0 to 10. Assess the candidate's actual response;
do not infer skills or provide a default score.

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

        text = _chat(get_groq_client(), self.model, prompt, max_tokens=1000)
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < 0 or end <= start:
                raise ValueError("The evaluation response did not contain JSON.")
            evaluation = json.loads(text[start:end])
            score_fields = (
                "score", "technical_accuracy", "completeness", "clarity",
                "communication_score",
            )
            for field in score_fields:
                value = evaluation.get(field)
                if not isinstance(value, (int, float)) or not 0 <= value <= 10:
                    raise ValueError(f"The evaluation response has an invalid {field}.")
            for field in ("feedback", "strengths", "improvements", "ideal_answer"):
                if not isinstance(evaluation.get(field), str) or not evaluation[field].strip():
                    raise ValueError(f"The evaluation response is missing {field}.")
            return evaluation
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.exception("AI answer evaluation response was invalid")
            raise HTTPException(
                status_code=502,
                detail="AI evaluation failed. Your answer was not saved; please try again.",
            ) from exc

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

        text = _chat(get_groq_client(), self.model, prompt, max_tokens=1500)
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < 0 or end <= start:
                raise ValueError("The performance analysis response did not contain JSON.")
            analysis = json.loads(text[start:end])
            if not isinstance(analysis.get("overall_assessment"), str):
                raise ValueError("The performance analysis response is incomplete.")
            return analysis
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.exception("AI performance analysis response was invalid")
            raise HTTPException(
                status_code=502,
                detail="AI report generation failed. Please try again.",
            ) from exc


ai_service = AIService()
