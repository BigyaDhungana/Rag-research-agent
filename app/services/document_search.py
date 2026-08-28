from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.document import DocumentChunk
from app.rag.embeddings import get_embedding_provider


def search_documents(db: Session, query: str, top_k: int = 5) -> list[dict]:
    provider = get_embedding_provider()
    query_embedding = provider.embed_query(query)

    stmt = (
        select(
            DocumentChunk,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
    )

    rows = db.execute(stmt).all()

    results = []
    for chunk, distance in rows:
        results.append(
            {
                "chunk_id": str(chunk.id),
                "content": chunk.content,
                "score": 1 - distance,  # cosine similarity from distance
                "document_id": str(chunk.document_id),
                "page": chunk.page_number,
                "source": "vector",
            }
        )
    return results
