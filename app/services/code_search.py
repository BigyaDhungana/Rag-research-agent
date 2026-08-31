from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.repository import CodeChunk, File
from app.rag.embeddings import get_embedding_provider


def search_code(
    db: Session, repository_id: str, query: str, top_k: int = 20
) -> list[dict]:
    provider = get_embedding_provider()
    query_embedding = provider.embed_query(query)

    stmt = (
        select(
            CodeChunk,
            File.relative_path,
            CodeChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(File, CodeChunk.file_id == File.id)
        .where(File.repository_id == repository_id)
        .order_by("distance")
        .limit(top_k)
    )

    rows = db.execute(stmt).all()

    results = []
    for chunk, relative_path, distance in rows:
        results.append(
            {
                "chunk_id": str(chunk.id),
                "content": chunk.content,
                "score": 1 - distance,
                "file_path": relative_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "symbol": chunk.chunk_metadata.get("symbol"),
                "node_type": chunk.chunk_metadata.get("node_type"),
                "parent_class": chunk.chunk_metadata.get("parent_class"),
                "source": "code_vector",
            }
        )
    return results
