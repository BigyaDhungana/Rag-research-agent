from sqlalchemy.orm import Session

from app.rag.llm import get_llm_provider, LLMProviderError
from app.rag.code_prompts import build_code_qa_prompt
from app.services.code_retrieval import retrieve_code

INSUFFICIENT_EVIDENCE_MARKER = (
    "I don't have enough information in this codebase to answer that."
)


def _build_code_context(results: list[dict]) -> tuple[str, list[dict]]:
    parts = []
    citations = []
    for i, r in enumerate(results, start=1):
        header = f"[Source {i}] {r['file_path']}"
        if r.get("symbol"):
            header += f" — {r['node_type']} `{r['symbol']}`"
            if r.get("parent_class"):
                header += f" (in class `{r['parent_class']}`)"
        header += f" (lines {r['start_line']}-{r['end_line']})"

        parts.append(f"{header}\n{r['content']}\n")
        citations.append(
            {
                "index": i,
                "file_path": r["file_path"],
                "symbol": r.get("symbol"),
                "parent_class": r.get("parent_class"),
                "start_line": r["start_line"],
                "end_line": r["end_line"],
                "chunk_id": r["chunk_id"],
            }
        )
    return "\n".join(parts), citations


def ask_repository(db: Session, repository_id: str, question: str) -> dict:
    retrieval = retrieve_code(db, repository_id, question)
    results = retrieval["results"]

    if not results:
        return {
            "question": question,
            "answer": INSUFFICIENT_EVIDENCE_MARKER,
            "citations": [],
        }

    context, citations = _build_code_context(results)
    prompt = build_code_qa_prompt(retrieval["rewritten_query"], context)

    try:
        answer = get_llm_provider().generate(prompt)
    except LLMProviderError as e:
        return {
            "question": question,
            "answer": f"Sorry, the AI service is temporarily unavailable ({e}).",
            "citations": [],
        }

    return {"question": question, "answer": answer, "citations": citations}
