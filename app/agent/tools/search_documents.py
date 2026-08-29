from sqlalchemy.orm import Session

from app.services.hybrid_retrieval import retrieve


def search_documents(db: Session, query: str, top_k: int = 5) -> list[dict]:
    """
    Wraps the existing retrieval pipeline (hybrid + RRF + rerank) as
    an agent tool. Deliberately reuses retrieve() rather than answer_query()
    as the agent's Synthesizer shold do its own reasoning over
    raw chunks, so we return chunks, not a pre-generated answer.
    """
    result = retrieve(db, query, final_k=top_k)
    return [
        {
            "content": r["content"],
            "document_id": r["document_id"],
            "page": r.get("page"),
            "chunk_id": r["chunk_id"],
            "score": r.get("rerank_score"),
            "source": "document",
        }
        for r in result["results"]
    ]
