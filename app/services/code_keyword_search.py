from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models.repository import CodeChunk, File


def code_keyword_search(
    db: Session, repository_id: str, query: str, top_k: int = 20
) -> list[dict]:
    tsquery = func.plainto_tsquery("english", query)
    tsvector = func.to_tsvector("english", CodeChunk.content)
    rank = func.ts_rank(tsvector, tsquery).label("rank")

    stmt = (
        select(CodeChunk, File.relative_path, rank)
        .join(File, CodeChunk.file_id == File.id)
        .where(File.repository_id == repository_id)
        .where(tsvector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(top_k)
    )

    rows = db.execute(stmt).all()

    results = []
    for chunk, relative_path, rank_score in rows:
        results.append(
            {
                "chunk_id": str(chunk.id),
                "content": chunk.content,
                "score": float(rank_score),
                "file_path": relative_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "symbol": chunk.chunk_metadata.get("symbol"),
                "node_type": chunk.chunk_metadata.get("node_type"),
                "parent_class": chunk.chunk_metadata.get("parent_class"),
                "source": "code_keyword",
            }
        )
    return results
