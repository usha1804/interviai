"""Resume parsing service — text extraction + AI structured analysis"""
import io
import json
import os
from typing import Optional
from fastapi import HTTPException

from app.services.ai_service import _chat, get_groq_client
from app.config import settings


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except ImportError:
        raise HTTPException(status_code=500, detail="pdfplumber not installed. Run: pip install pdfplumber")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        text_parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for section in doc.sections:
            for part in (section.header, section.footer):
                text_parts.extend(
                    paragraph.text.strip()
                    for paragraph in part.paragraphs
                    if paragraph.text.strip()
                )
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = "\n".join(
                        paragraph.text.strip()
                        for paragraph in cell.paragraphs
                        if paragraph.text.strip()
                    )
                    if cell_text:
                        text_parts.append(cell_text)
        return "\n".join(text_parts).strip()
    except ImportError:
        raise HTTPException(status_code=500, detail="python-docx not installed. Run: pip install python-docx")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse DOCX: {str(e)}")


def extract_text(file_bytes: bytes, content_type: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf" or content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if ext in ("docx",) or "wordprocessingml" in content_type:
        return extract_text_from_docx(file_bytes)
    if ext == "doc":
        raise HTTPException(status_code=400, detail=".doc format not supported. Please convert to PDF or DOCX.")
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


def parse_resume_with_ai(resume_text: str) -> dict:
    """Use Groq to extract structured data from raw resume text."""
    client = get_groq_client()

    prompt = f"""You are an expert resume parser.

Analyze the following resume text and extract structured information.

Resume Text:
\"\"\"
{resume_text[:4000]}
\"\"\"

Return ONLY this JSON (no extra text):
{{
    "name": "<full name or null>",
    "email": "<email or null>",
    "skills": ["skill1", "skill2", "..."],
    "technologies": ["tech1", "tech2", "..."],
    "projects": ["Project Name 1", "Project Name 2"],
    "experience": [
        {{"company": "...", "role": "...", "duration": "..."}}
    ],
    "education": [
        {{"degree": "...", "institution": "...", "year": "..."}}
    ],
    "summary": "<2-sentence professional summary>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1500)
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        return {
            "name": None, "email": None,
            "skills": [], "technologies": [],
            "projects": [], "experience": [],
            "education": [], "summary": ""
        }


def generate_resume_questions(parsed_data: dict, difficulty: str = "MEDIUM") -> dict:
    """Generate interview questions strictly based on resume content."""
    client = get_groq_client()

    skills = ", ".join(parsed_data.get("skills", []) + parsed_data.get("technologies", []))
    projects = ", ".join(parsed_data.get("projects", []))
    experience = parsed_data.get("experience", [])
    exp_text = "; ".join(
        f"{e.get('role', '')} at {e.get('company', '')}" for e in experience
    ) if experience else "Not specified"

    prompt = f"""You are an expert technical interviewer.

Based ONLY on this candidate's resume, generate targeted interview questions.

Candidate Profile:
- Skills & Technologies: {skills or "Not specified"}
- Projects: {projects or "Not specified"}
- Experience: {exp_text}
- Difficulty: {difficulty}

Generate exactly:
- 5 technical questions (based on their specific skills/technologies)
- 5 project-based questions (based on their actual projects)
- 3 behavioral questions (relevant to their experience level)

Return ONLY this JSON:
{{
    "technical": ["q1", "q2", "q3", "q4", "q5"],
    "project_based": ["q1", "q2", "q3", "q4", "q5"],
    "behavioral": ["q1", "q2", "q3"]
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1500)
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        return {
            "technical": ["Explain a challenging technical problem you solved."],
            "project_based": ["Walk me through your most complex project."],
            "behavioral": ["Tell me about yourself."]
        }
