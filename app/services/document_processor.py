from sqlalchemy.orm import Session

from app.db.models.document import Document, DocumentChunk, DocumentStatus
from app.services.pdf_extractor import extract_text_by_page
from app.services.chunking import chunk_text
from app.rag.embeddings import get_embedding_provider


def process_document(db: Session, document: Document) -> None:
    try:
        document.status = DocumentStatus.processing
        db.commit()

        pages = extract_text_by_page(document.storage_path)

        raw_chunks = chunk_text(pages)

        if not raw_chunks:
            document.status = DocumentStatus.failed
            db.commit()
            return

        provider = get_embedding_provider()
        contents = [c["content"] for c in raw_chunks]

        BATCH_SIZE = 100
        all_embeddings = []
        for i in range(0, len(contents), BATCH_SIZE):
            batch = contents[i : i + BATCH_SIZE]
            batch_embeddings = provider.embed_documents(batch)
            all_embeddings.extend(batch_embeddings)

        db.bulk_insert_mappings(
            DocumentChunk,
            [
                {
                    "document_id": document.id,
                    "content": raw_chunk["content"],
                    "chunk_index": raw_chunk["chunk_index"],
                    "page_number": raw_chunk["page_number"],
                    "chunk_metadata": {
                        "source": document.filename,
                        "page": raw_chunk["page_number"],
                        "chunk_index": raw_chunk["chunk_index"],
                    },
                    "embedding": embedding,
                }
                for raw_chunk, embedding in zip(raw_chunks, all_embeddings)
            ],
        )

        # 6. Mark as ready
        document.status = DocumentStatus.ready
        db.commit()

    except Exception:
        document.status = DocumentStatus.failed
        db.commit()
        raise
