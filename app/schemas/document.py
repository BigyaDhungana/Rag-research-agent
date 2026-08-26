import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.db.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    title: str | None
    mime_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)