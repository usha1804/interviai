"""
Vector service — ChromaDB wrapper for all collections.
Persists to ./chroma_db directory inside the backend folder.
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.services.embedding_service import embed_texts, embed_text

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=os.path.abspath(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _col(name: str):
    return _get_client().get_or_create_collection(name)


# ── Insert ────────────────────────────────────────────────────────

def upsert_documents(
    collection: str,
    doc_ids: List[str],
    texts: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
):
    embeddings = embed_texts(texts)
    col = _col(collection)
    col.upsert(
        ids=doc_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas or [{} for _ in texts],
    )


# ── Search ────────────────────────────────────────────────────────

def similarity_search(
    collection: str,
    query: str,
    n_results: int = 5,
    where: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    col = _col(collection)
    count = col.count()
    if count == 0:
        return []
    n = min(n_results, count)
    kwargs = {"query_embeddings": [embed_text(query)], "n_results": n}
    if where:
        kwargs["where"] = where
    results = col.query(**kwargs)
    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "text": doc,
            "id": results["ids"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "distance": results["distances"][0][i] if results.get("distances") else 0,
        })
    return output


# ── Delete ────────────────────────────────────────────────────────

def delete_documents(collection: str, doc_ids: List[str]):
    _col(collection).delete(ids=doc_ids)


def delete_by_metadata(collection: str, where: Dict):
    col = _col(collection)
    results = col.get(where=where)
    if results["ids"]:
        col.delete(ids=results["ids"])
