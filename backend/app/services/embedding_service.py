"""
Embedding service — generates vector embeddings using sentence-transformers.
Model runs locally, no API key required.
"""
from typing import List
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of strings, return list of float vectors."""
    model = _get_model()
    return model.encode(texts, convert_to_numpy=True).tolist()


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
