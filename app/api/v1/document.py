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
