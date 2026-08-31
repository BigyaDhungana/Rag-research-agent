from sqlalchemy.orm import Session

from app.rag.query_rewriter import get_query_rewriter
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.reranker import get_reranker
from app.services.code_search import search_code
from app.services.code_keyword_search import code_keyword_search


def hybrid_code_search(
    db: Session, repository_id: str, query: str, top_k_per_method: int = 50
) -> dict:
    rewritten_query = get_query_rewriter().rewrite(query)

    vector_results = search_code(
        db, repository_id, rewritten_query, top_k=top_k_per_method
    )
    keyword_results = code_keyword_search(
        db, repository_id, rewritten_query, top_k=top_k_per_method
    )

    candidates: dict[str, dict] = {}
    for rank, r in enumerate(vector_results):
        cid = r["chunk_id"]
        candidates[cid] = {
            **r,
            "vector_score": r["score"],
            "vector_rank": rank,
            "keyword_score": None,
            "keyword_rank": None,
        }

    for rank, r in enumerate(keyword_results):
        cid = r["chunk_id"]
        if cid in candidates:
            candidates[cid]["keyword_score"] = r["score"]
            candidates[cid]["keyword_rank"] = rank
        else:
            candidates[cid] = {
                **r,
                "vector_score": None,
                "vector_rank": None,
                "keyword_score": r["score"],
                "keyword_rank": rank,
            }

    return {"rewritten_query": rewritten_query, "candidates": list(candidates.values())}


def retrieve_code(
    db: Session, repository_id: str, query: str, fused_k: int = 20, final_k: int = 5
) -> dict:
    hybrid = hybrid_code_search(db, repository_id, query)
    fused = reciprocal_rank_fusion(hybrid["candidates"])
    reranked = get_reranker().rerank(
        hybrid["rewritten_query"], fused[:fused_k], top_k=final_k
    )
    return {"rewritten_query": hybrid["rewritten_query"], "results": reranked}
