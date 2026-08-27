from sqlalchemy.orm import Session

from app.db.models.document import Document, DocumentStatus
from app.core.storage import save_file

ALLOWED_MIME_TYPES = {"application/pdf"}

import os
import magic  
from sqlalchemy.exc import SQLAlchemyError


def create_document(
    db: Session, filename: str, mime_type: str, content: bytes
) -> Document:
    detected_mime = magic.from_buffer(content, mime=True)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"File signature '{detected_mime}' is not allowed. "
            f"Received header claimed: {mime_type}"
        )

    storage_path = save_file(filename, content)

    try:
        document = Document(
            filename=filename,
            mime_type=detected_mime, 
            file_size=len(content),
            storage_path=storage_path,
            status=DocumentStatus.pending,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    except (SQLAlchemyError, Exception) as e:
        # Rollback the filesystem if DB fails
        if os.path.exists(storage_path):
            os.remove(storage_path)
        db.rollback() 
        raise e
