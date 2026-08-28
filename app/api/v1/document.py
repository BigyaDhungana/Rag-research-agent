from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
)
from app.services.document_service import create_document
from app.services.document_processor import process_document
from app.services.document_search import search_documents
from app.services.hybrid_retrieval import hybrid_search, retrieve

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()

    try:
        document = create_document(
            db=db,
            filename=file.filename,
            mime_type=file.content_type,
            content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    process_document(db, document)
    db.refresh(document)

    return document


@router.post("/search", response_model=DocumentSearchResponse)
def search(
    request: DocumentSearchRequest,
    db: Session = Depends(get_db),
):
    results = search_documents(db, request.query, request.top_k)
    return DocumentSearchResponse(results=results)


@router.post("/search/hybrid")
def search_hybrid(
    request: DocumentSearchRequest,
    db: Session = Depends(get_db),
):
    return hybrid_search(db, request.query, top_k_per_method=request.top_k)


@router.post("/search/rerank")
def search_reranked(
    request: DocumentSearchRequest,
    db: Session = Depends(get_db),
):
    return retrieve(db, request.query)
