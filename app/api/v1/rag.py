from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_query import answer_query

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/query", response_model=RAGQueryResponse)
def query(request: RAGQueryRequest, db: Session = Depends(get_db)):
    return answer_query(db, request.question)