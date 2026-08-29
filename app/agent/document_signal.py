from sqlalchemy.orm import Session

from app.services.keyword_search import keyword_search
from app.services.document_search import search_documents


def get_document_signal(db: Session, objective: str, threshold: int = 1) -> str:
    """
    Cheap pre-check so the planner has real evidence, not a guess, aboutwhether search_documents is worth a step. Runs BOTH keyword and vector
    search directly (not the full hybrid_search/retrieve pipeline — no RRF,
    no reranker) since this only needs a yes/no-ish signal, not a ranked
    result set. Cheap enough to run unconditionally before every plan.
    """
    keyword_hits = keyword_search(db, objective, top_k=threshold)
    vector_hits = search_documents(db, objective, top_k=threshold)

    total_hits = len(keyword_hits) + len(vector_hits)

    if total_hits == 0:
        return "No matching content found in the user's uploaded documents."

    # Give the planner a taste of what matched, not just a count — helps it
    # judge relevance rather than treating any nonzero hit as a green light.
    sample = (vector_hits or keyword_hits)[0]
    snippet = sample["content"][:150].replace("\n", " ")
    return f'Found {total_hits} potentially relevant chunk(s). Example: "{snippet}..."'
