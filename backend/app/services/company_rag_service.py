"""Company-specific RAG helpers for generating interview questions using company context."""
import json
from typing import Dict, List, Optional, Any

from groq import Groq

from app.config import settings
from app.services.ai_service import _chat
from app.services.ingestion_service import build_collection_name, clean_text, chunk_text
from app.services.vector_service import similarity_search, upsert_documents

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
) -> Dict[str, Any]:
    """Generate company-specific interview questions with grounded context retrieval."""
    question_types = question_types or ["Technical", "Behavioral", "Coding", "System Design"]
    context_query = f"{role or ''} {experience or ''} {' '.join(skills or [])} {job_description or ''}".strip()
    company_context = retrieve_company_context(company or "", context_query, k=4) if company else ""

    prompt = f"""You are an experienced interviewer.
Use ONLY the retrieved context below. Do not invent company-specific policies.
If the context is too thin, generate a generic interview question and clearly mark it as generic.

COMPANY: {company or 'Generic'}
ROLE: {role or 'Any role'}
EXPERIENCE: {experience or 'Any'}
SKILLS: {', '.join(skills or []) or 'Not provided'}
RESUME CONTEXT: {resume_text or 'Not provided'}
JOB DESCRIPTION: {job_description or 'Not provided'}
RETRIEVED COMPANY CONTEXT:
{company_context or 'No company-specific context available.'}

Generate 4 questions in this JSON format:
{{"questions":[{{"type":"Technical","question":"...","company_specific":true}}]}}
"""

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1800)
    except Exception:
        text = ""

    if not text:
        return {"questions": [
            {"type": item, "question": f"{item} question for {company or 'the target company'} role", "company_specific": False}
            for item in question_types[:4]
        ]}

    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        payload = json.loads(text[start:end])
        return payload
    except Exception:
        return {"questions": [{"type": item, "question": f"{item} question for {company or 'the target company'} role", "company_specific": False} for item in question_types[:4]]}
