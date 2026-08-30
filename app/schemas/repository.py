import uuid
from pydantic import BaseModel

class RepositoryCreateRequest(BaseModel):
    url: str

class RepositoryResponse(BaseModel):
    id: uuid.UUID
    url: str
    name: str
    status: str
    error_message: str | None = None

    class Config:
        from_attributes = True