from sqlalchemy.orm import Session

from app.rag.query_rewriter import get_query_rewriter
from app.services.document_search import search_documents
from app.services.keyword_search import keyword_search


def hybrid_search(db: Session, query: str, top_k_per_method: int = 20) -> dict:
    """
    Rewrite the query, run vector search and keyword search independently, 
    and merge into 1 deduplicated candidate set.
    Not fused into a single ranked list yet
    """
    rewritten_query = get_query_rewriter().rewrite(query)

    vector_results = search_documents(db, rewritten_query, top_k=top_k_per_method)
    keyword_results = keyword_search(db, rewritten_query, top_k=top_k_per_method)

    candidates: dict[str, dict] = {}

    for rank, result in enumerate(vector_results):
        cid = result["chunk_id"]
        candidates[cid] = {
            **result,
            "vector_score": result["score"],
            "vector_rank": rank,
            "keyword_score": None,
            "keyword_rank": None,
        }

    for rank, result in enumerate(keyword_results):
        cid = result["chunk_id"]
        if cid in candidates:
            candidates[cid]["keyword_score"] = result["score"]
            candidates[cid]["keyword_rank"] = rank
        else:
            candidates[cid] = {
                **result,
                "vector_score": None,
                "vector_rank": None,
                "keyword_score": result["score"],
                "keyword_rank": rank,
            }

    return {
        "original_query": query,
        "rewritten_query": rewritten_query,
        "candidates": list(candidates.values()),
    }
