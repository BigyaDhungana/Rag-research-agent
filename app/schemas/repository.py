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


class CodeSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class CodeSearchResponse(BaseModel):
    results: list[dict]  


class CodeAskRequest(BaseModel):
    question: str


class CodeAskResponse(BaseModel):
    question: str
    answer: str
    citations: list[dict]
