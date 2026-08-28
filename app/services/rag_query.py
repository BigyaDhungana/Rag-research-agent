from sqlalchemy.orm import Session

from app.rag.context_builder import build_context
from app.rag.llm import get_llm_provider
from app.rag.prompts import build_prompt
from app.services.hybrid_retrieval import retrieve

INSUFFICIENT_EVIDENCE_MARKER = "I don't have sufficient evidence in the provided documents to answer this question."


def answer_query(db: Session, question: str) -> dict:
    retrieval = retrieve(db, question)
    results = retrieval["results"]

    if not results:
        return {
            "question": question,
            "answer": INSUFFICIENT_EVIDENCE_MARKER,
            "citations": [],
            "used_documents": False,
        }

    context, citations = build_context(results)
    prompt = build_prompt(retrieval["rewritten_query"], context)

    answer = get_llm_provider().generate(prompt)

    is_insufficient = INSUFFICIENT_EVIDENCE_MARKER in answer

    return {
        "question": question,
        "answer": answer,
        "citations": [] if is_insufficient else citations,
        "used_documents": not is_insufficient,
    }