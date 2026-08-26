from sqlalchemy.orm import Session

from app.db.models.document import Document, DocumentStatus
from app.core.storage import save_file

ALLOWED_MIME_TYPES = {"application/pdf"}


def create_document(
    db: Session, filename: str, mime_type: str, content: bytes
) -> Document:
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {mime_type}")

    storage_path = save_file(filename, content)

    document = Document(
        filename=filename,
        mime_type=mime_type,
        file_size=len(content),
        storage_path=storage_path,
        status=DocumentStatus.pending,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
