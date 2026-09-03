from sqlalchemy.orm import Session

from app.rag.query_rewriter import get_query_rewriter
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.reranker import get_reranker
from app.services.document_search import search_documents
from app.services.keyword_search import keyword_search

from langfuse import observe


def hybrid_search(db: Session, query: str, top_k_per_method: int = 100) -> dict:
    """
    Rewrite the query, run vector + keyword search independently,
    merge into ONE deduplicated candidate set.
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

@observe(name="retrieve")
def retrieve(
    db: Session,
    query: str,
    candidate_k: int = 100,
    fused_k: int = 20,
    final_k: int = 5,
) -> dict:
    """
    full pipeline — 100 (per method) -> hybrid merge -> RRF ->
    top 20 -> cross-encoder rerank -> top 5.
    """
    hybrid = hybrid_search(db, query, top_k_per_method=candidate_k)

    fused = reciprocal_rank_fusion(hybrid["candidates"])
    top_fused = fused[:fused_k]

    reranked = get_reranker().rerank(
        hybrid["rewritten_query"], top_fused, top_k=final_k
    )

    return {
        "original_query": hybrid["original_query"],
        "rewritten_query": hybrid["rewritten_query"],
        "results": reranked,
    }
