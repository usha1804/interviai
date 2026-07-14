"""Utilities for cleaning, chunking, and organizing company knowledge documents."""
import re
from typing import List, Optional


def build_collection_name(company: str) -> str:
    """Create a stable Chroma collection name from a company name."""
    slug = re.sub(r"[^a-z0-9]+", "_", (company or "company").strip().lower()).strip("_")
    return f"{slug}_collection" if slug else "company_collection"


def clean_text(text: str) -> str:
    """Normalize whitespace and remove obvious formatting noise."""
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text)
    cleaned = re.sub(r"[\u0000-\u001f]", " ", cleaned)
    return cleaned.strip()


def chunk_text(text: str, size: int = 400, overlap: int = 80) -> List[str]:
    """Split long text into smaller overlapping chunks."""
    cleaned = clean_text(text)
    if not cleaned:
        return []

    words = cleaned.split()
    if len(words) <= size:
        return [cleaned] if len(cleaned) > 30 else []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + size)
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start += size - overlap
    return [c for c in chunks if len(c.strip()) > 30]
