from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.repository import (
    RepositoryCreateRequest,
    RepositoryResponse,
    CodeSearchRequest,
    CodeSearchResponse,
    CodeAskRequest,
    CodeAskResponse,
)
from app.services.repo_service import ingest_repository
from app.services.code_retrieval import retrieve_code
from app.services.code_qa import ask_repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=RepositoryResponse)
def create_repository(request: RepositoryCreateRequest, db: Session = Depends(get_db)):
    return ingest_repository(db, request.url)


@router.post("/{repository_id}/search", response_model=CodeSearchResponse)
def search_repository(
    repository_id: str, request: CodeSearchRequest, db: Session = Depends(get_db)
):
    result = retrieve_code(db, repository_id, request.query, final_k=request.top_k)
    return CodeSearchResponse(results=result["results"])


@router.post("/{repository_id}/ask", response_model=CodeAskResponse)
def ask_repository_endpoint(
    repository_id: str, request: CodeAskRequest, db: Session = Depends(get_db)
):
    return ask_repository(db, repository_id, request.question)
