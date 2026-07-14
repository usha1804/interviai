"""
RAG service — Resume + JD ingestion, chunking, retrieval, question generation.
"""
import json
import re
from typing import List, Dict, Optional
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat
from app.services.vector_service import upsert_documents, similarity_search, delete_by_metadata

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


# ── Text Chunking ─────────────────────────────────────────────────

def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i: i + size])
        chunks.append(chunk)
        i += size - overlap
    return [c for c in chunks if len(c.strip()) > 30]


# ── Ingest ────────────────────────────────────────────────────────

def ingest_resume(user_id: int, resume_id: int, text: str):
    """Chunk resume text and store in ChromaDB."""
    delete_by_metadata("resumes", {"user_id": str(user_id)})
    chunks = _chunk_text(text)
    ids = [f"resume_{resume_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [{"user_id": str(user_id), "resume_id": str(resume_id), "chunk": i} for i in range(len(chunks))]
    upsert_documents("resumes", ids, chunks, metas)


def ingest_job_description(user_id: int, jd_id: int, text: str):
    """Chunk JD text and store in ChromaDB."""
    delete_by_metadata("job_descriptions", {"user_id": str(user_id)})
    chunks = _chunk_text(text)
    ids = [f"jd_{jd_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [{"user_id": str(user_id), "jd_id": str(jd_id), "chunk": i} for i in range(len(chunks))]
    upsert_documents("job_descriptions", ids, chunks, metas)


# ── Retrieve ──────────────────────────────────────────────────────

def retrieve_resume_context(user_id: int, query: str, k: int = 4) -> str:
    results = similarity_search("resumes", query, n_results=k, where={"user_id": str(user_id)})
    return "\n\n".join(r["text"] for r in results)


def retrieve_jd_context(user_id: int, query: str, k: int = 4) -> str:
    results = similarity_search("job_descriptions", query, n_results=k, where={"user_id": str(user_id)})
    return "\n\n".join(r["text"] for r in results)


# ── RAG Question Generation ───────────────────────────────────────

def generate_rag_questions(
    user_id: int,
    question_types: List[str],
    difficulty: str = "MEDIUM",
    company: Optional[str] = None,
    asked_questions: Optional[List[str]] = None,
) -> Dict:
    """Generate interview questions grounded in resume + JD context."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    resume_ctx = retrieve_resume_context(user_id, "skills experience projects education")
    jd_ctx = retrieve_jd_context(user_id, "required skills responsibilities qualifications")

    asked_str = "\n".join(f"- {q}" for q in (asked_questions or [])[:20])
    types_str = ", ".join(question_types)
    company_str = f"Company: {company}\nAlign questions with {company}'s known interview style.\n" if company else ""

    prompt = f"""You are a Senior Technical Interviewer with 15 years of experience.

{company_str}
RESUME CONTEXT:
{resume_ctx or "No resume uploaded yet."}

JOB DESCRIPTION CONTEXT:
{jd_ctx or "No job description uploaded yet."}

DIFFICULTY: {difficulty}
QUESTION TYPES NEEDED: {types_str}
ALREADY ASKED (do NOT repeat):
{asked_str or "None"}

Generate exactly 2 questions per type listed. Questions must be:
- Directly grounded in the resume and JD context above
- Specific to the candidate's actual projects, skills, and experience
- Progressive in difficulty

Return ONLY this JSON:
{{
    "questions": [
        {{
            "type": "<type>",
            "question": "<question text>",
            "context_used": "<which part of resume/JD informed this>",
            "difficulty": "{difficulty}"
        }}
    ]
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=2000)
    try:
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"questions": []}


# ── RAG Answer Evaluation ─────────────────────────────────────────

def evaluate_answer_with_context(
    user_id: int,
    question: str,
    user_answer: str,
    category: str,
) -> Dict:
    """Evaluate answer using resume + JD as grounding context."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    resume_ctx = retrieve_resume_context(user_id, question, k=3)
    jd_ctx = retrieve_jd_context(user_id, question, k=2)

    prompt = f"""You are an expert technical interviewer evaluating a candidate's answer.

RESUME CONTEXT: {resume_ctx or "N/A"}
JOB DESCRIPTION CONTEXT: {jd_ctx or "N/A"}
QUESTION: {question}
CANDIDATE'S ANSWER: {user_answer}
CATEGORY: {category}

Evaluate considering the candidate's background from their resume and the job requirements.

Return ONLY this JSON:
{{
    "score": <0-10>,
    "technical_accuracy": <0-10>,
    "completeness": <0-10>,
    "clarity": <0-10>,
    "communication_score": <0-10>,
    "resume_relevance": <0-10>,
    "feedback": "<2-3 sentences>",
    "strengths": "<key strengths>",
    "improvements": "<areas to improve>",
    "ideal_answer": "<model answer 3-5 sentences>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1200)
    try:
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "score": 5.0, "technical_accuracy": 5.0, "completeness": 5.0,
            "clarity": 5.0, "communication_score": 5.0, "resume_relevance": 5.0,
            "feedback": "Unable to evaluate.", "strengths": "Attempted the question.",
            "improvements": "Provide more detail.", "ideal_answer": "N/A",
        }
