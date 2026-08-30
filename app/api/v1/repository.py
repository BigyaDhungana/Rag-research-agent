from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.repository import RepositoryCreateRequest, RepositoryResponse
from app.services.repo_service import ingest_repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=RepositoryResponse)
def create_repository(request: RepositoryCreateRequest, db: Session = Depends(get_db)):
    return ingest_repository(db, request.url)
