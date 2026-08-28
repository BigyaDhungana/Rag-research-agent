from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models.document import DocumentChunk


def keyword_search(db: Session, query: str, top_k: int = 20) -> list[dict]:
    """
    Postgres full-text search over chunk content using plainto_tsquery,
    ranked with ts_rank. Computed on the fly via to_tsvector rather than a
    stored column, backed by a functional GIN index
    """
    tsquery = func.plainto_tsquery("english", query)
    tsvector = func.to_tsvector("english", DocumentChunk.content)
    rank = func.ts_rank(tsvector, tsquery).label("rank")

    stmt = (
        select(DocumentChunk, rank)
        .where(tsvector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(top_k)
    )

    rows = db.execute(stmt).all()

    results = []
    for chunk, rank_score in rows:
        results.append(
            {
                "chunk_id": str(chunk.id),
                "content": chunk.content,
                "score": float(rank_score),
                "document_id": str(chunk.document_id),
                "page": chunk.page_number,
                "source": "keyword",
            }
        )
    return results
