"""Company-specific RAG helpers for generating interview questions using company context."""
import json
import re
from typing import Dict, List, Optional, Any

from app.config import settings
from app.services.ai_service import _chat, get_groq_client
from app.services.ingestion_service import build_collection_name, clean_text, chunk_text

SUPPORTED_COMPANIES = [
    "Google",
    "Amazon",
    "Microsoft",
    "Meta",
    "Apple",
    "Netflix",
    "Accenture",
    "TCS",
    "Infosys",
    "Wipro",
    "Capgemini",
    "Deloitte",
    "Cognizant",
    "IBM",
    "Oracle",
    "Salesforce",
    "Adobe",
    "Uber",
    "Flipkart",
    "Atlassian",
]


def ingest_company_document(company: str, text: str, source: str = "manual") -> Dict[str, Any]:
    """Store company knowledge text into a dedicated Chroma collection."""
    from app.services.vector_service import upsert_documents

    collection = build_collection_name(company)
    cleaned = clean_text(text)
    chunks = chunk_text(cleaned)
    if not chunks:
        return {"collection": collection, "stored": 0}

    ids = [f"{collection}_chunk_{i}" for i in range(len(chunks))]
    metadata = [{
        "company": company,
        "source": source,
        "chunk": i,
    } for i in range(len(chunks))]
    upsert_documents(collection, ids, chunks, metadata)
    return {"collection": collection, "stored": len(chunks)}


def retrieve_company_context(company: str, query: str, k: int = 5) -> str:
    """Retrieve relevant context from a company-specific collection."""
    if not company:
        return ""
    from app.services.vector_service import similarity_search

    collection = build_collection_name(company)
    results = similarity_search(collection, query, n_results=k, where={"company": company})
    return "\n\n".join(item["text"] for item in results if item.get("text"))


def generate_company_questions(
    company: Optional[str],
    role: Optional[str],
    experience: Optional[str],
    skills: Optional[List[str]],
    resume_text: Optional[str],
    job_description: Optional[str],
    question_types: Optional[List[str]] = None,
    difficulty: str = "MEDIUM",
    interview_round: Optional[str] = None,
    previous_questions: Optional[List[str]] = None,
    question_number: int = 1,
    question_count: Optional[int] = None,
    interview_duration_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate and validate one configuration-specific company interview question."""
    question_types = question_types or ["Technical"]
    category = question_types[0]
    context_query = f"{role or ''} {experience or ''} {' '.join(skills or [])} {job_description or ''}".strip()
    company_context = retrieve_company_context(company or "", context_query, k=4) if company else ""

    prompt = f"""You are an experienced interviewer creating a realistic practice question.
Use the retrieved company context only for company-specific facts. If it is absent or insufficient,
ask a strong role-relevant question without inventing company facts. These are practice questions,
not official or guaranteed interview questions.

COMPANY: {company or 'Generic'}
ROLE: {role or 'Not provided'}
EXPERIENCE LEVEL: {experience or 'Not provided'}
INTERVIEW ROUND: {interview_round or category}
CATEGORY: {category}
DIFFICULTY: {difficulty}
QUESTION POSITION: {question_number} of {question_count or 'unspecified'}
TOTAL INTERVIEW DURATION: {interview_duration_minutes or 'unspecified'} minutes
TECHNICAL SKILLS: {', '.join(skills or []) or 'Use the role and job description'}
RESUME CONTEXT (use only if relevant): {resume_text or 'Not provided'}
JOB DESCRIPTION: {job_description or 'Not provided'}
RETRIEVED COMPANY CONTEXT:
{company_context or 'No company-specific context available.'}
QUESTIONS ALREADY ASKED (do not repeat or paraphrase):
{json.dumps(previous_questions or [])}

Generate exactly one specific, technically sound question matching the role, experience, round,
and difficulty. Progress naturally from previous questions and account for the overall interview
duration. Avoid vague prompts and placeholders such as "question for [company] role".
Return only valid JSON with this shape:
{{"question":"...","topic":"...","category":"...","difficulty":"{difficulty}","context":"... or empty string","evaluation_criteria":["...","..."],"company_specific":true}}
"""

    last_error = None
    for _ in range(2):
        try:
            text = _chat(get_groq_client(), settings.GROQ_MODEL, prompt, max_tokens=700)
            start, end = text.find("{"), text.rfind("}") + 1
            if start < 0 or end <= start:
                raise ValueError("The question generator did not return a JSON object.")
            payload = json.loads(text[start:end])
            question = payload.get("question")
            criteria = payload.get("evaluation_criteria")
            if (
                not isinstance(question, str)
                or len(question.strip()) < 20
                or not isinstance(payload.get("topic"), str)
                or not payload["topic"].strip()
                or not isinstance(criteria, list)
                or not criteria
                or not all(isinstance(item, str) and item.strip() for item in criteria)
                or not isinstance(payload.get("category"), str)
                or not payload["category"].strip()
                or not isinstance(payload.get("difficulty"), str)
            ):
                raise ValueError("The generated question is missing required structured fields.")
            if re.search(r"\b(?:technical|behavioral|coding)?\s*question for .+ role\b", question, re.I):
                raise ValueError("The generated question is a generic placeholder.")
            if any(question.strip().casefold() == old.strip().casefold() for old in previous_questions or []):
                raise ValueError("The generated question repeats a question already asked.")
            payload["question"] = question.strip()
            payload["topic"] = payload["topic"].strip()
            payload["category"] = payload["category"].strip()
            payload["difficulty"] = difficulty
            payload["context"] = payload.get("context", "") if isinstance(payload.get("context", ""), str) else ""
            payload["evaluation_criteria"] = [item.strip() for item in criteria]
            payload["company_specific"] = bool(payload.get("company_specific", False) and company_context)
            return {"questions": [payload]}
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Unable to generate a valid interview question: {last_error}") from last_error
