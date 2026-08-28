MAX_CONTEXT_CHARS = 8000 


def build_context(chunks: list[dict]) -> tuple[str, list[dict]]:
    """
    Takes the top-K reranked chunks from retrieve() and produces:
    - a single formatted context string, each chunk numbered as a source
      the prompt can point the model at
    - a citations list (document_id, page, chunk_id) in the SAME order,
      so citation index N in the answer maps to citations[N-1]

    Dedupes on chunk_id (retrieve() shouldn't produce duplicates post-RRF,
    but this stays defensive rather than assuming upstream never changes).
    Truncates to MAX_CONTEXT_CHARS, dropping whole chunks from the end
    rather than cutting a chunk mid-sentence.
    """
    seen_ids: set[str] = set()
    deduped = []
    for chunk in chunks:
        cid = chunk["chunk_id"]
        if cid not in seen_ids:
            seen_ids.add(cid)
            deduped.append(chunk)

    context_parts = []
    citations = []
    total_chars = 0

    for i, chunk in enumerate(deduped, start=1):
        block = f"[Source {i}]\n{chunk['content']}\n"
        if total_chars + len(block) > MAX_CONTEXT_CHARS and context_parts:
            break  # keep at least one source even if it alone exceeds the cap
        context_parts.append(block)
        total_chars += len(block)
        citations.append(
            {
                "index": i,
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "page": chunk.get("page"),
            }
        )

    return "\n".join(context_parts), citations
