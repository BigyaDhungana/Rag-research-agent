from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.repository import File, CodeChunk
from app.rag.embeddings import get_embedding_provider
from app.services.code_chunking import chunk_code_file

from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.repository import File, CodeChunk
from app.rag.embeddings import get_embedding_provider
from app.services.code_chunking import chunk_code_file


def process_repository_files(
    db: Session, repo_local_path: str, files: list[File]
) -> None:
    provider = get_embedding_provider()

    for file in files:
        full_path = Path(repo_local_path) / file.relative_path
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        raw_chunks = chunk_code_file(content, file.language or "")
        raw_chunks = [c for c in raw_chunks if c["content"].strip()]
        if not raw_chunks:
            continue

        # Batch-embed all of this file's chunks 
        texts = [c["content"] for c in raw_chunks]
        embeddings = provider.embed_documents(texts)

        for i, (chunk, embedding) in enumerate(zip(raw_chunks, embeddings)):
            db.add(
                CodeChunk(
                    file_id=file.id,
                    content=chunk["content"],
                    chunk_index=i,
                    start_line=chunk["start_line"],
                    end_line=chunk["end_line"],
                    chunk_metadata={
                        **chunk["chunk_metadata"],
                        "file_path": file.relative_path,
                    },
                    embedding=embedding,
                )
            )

        db.commit()
