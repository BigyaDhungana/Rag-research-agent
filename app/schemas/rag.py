from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    question: str


class Citation(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    page: int | None = None


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    used_documents: bool