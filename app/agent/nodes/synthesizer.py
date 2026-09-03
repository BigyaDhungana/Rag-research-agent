from app.agent.state import AgentState
from app.rag.llm import get_llm_provider

from langfuse import observe

SYNTHESIS_PROMPT_TEMPLATE = """You are a research synthesizer. Combine the numbered sources below into a clear, well-organized answer to the objective. Sources are tagged as either [WEB] or [DOCUMENT].

Rules:
- Cite every claim inline using [Source N] immediately after it.
- Draw on both web and document sources where both are relevant — don't ignore one category just because the other has more sources.
- If sources conflict, note the disagreement rather than silently picking one.
- If a step's evidence is missing or errored, work with what's available and don't invent facts to fill the gap.
- Do not fabricate source numbers or claims unsupported by the sources.

Objective: {objective}

Sources:
{sources}

Answer:"""


def _flatten_evidence(tool_results: list[dict]) -> tuple[str, list[dict]]:
    """
    Turns tool_results into numbered [Source N] blocks (mirroring the RAG
    pipeline's context_builder ) plus a parallel citations list, so
    citation index N in the answer maps to citations[N-1] regardless of
    which tool it came from.
    """
    sources_text = []
    citations = []
    n = 0

    for r in tool_results:
        if r["error"]:
            continue

        label = "WEB" if r["tool"] in ("search_web", "fetch_page") else "DOCUMENT"
        items = r["output"] if isinstance(r["output"], list) else [r["output"]]

        for item in items:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not content:
                continue

            n += 1
            sources_text.append(f"[Source {n}] [{label}]\n{content}\n")

            citation = {"index": n, "tool": r["tool"], "query": r["query"]}
            if label == "WEB":
                citation["url"] = item.get("url")
                citation["title"] = item.get("title")
            else:
                citation["document_id"] = item.get("document_id")
                citation["page"] = item.get("page")
                citation["chunk_id"] = item.get("chunk_id")
            citations.append(citation)

    return "\n".join(sources_text), citations

@observe(name="synthesize")
def synthesizer_node(state: AgentState) -> AgentState:
    sources_text, citations = _flatten_evidence(state["tool_results"])

    if not sources_text:
        return {
            **state,
            "final_answer": "I couldn't gather enough evidence from web search or your documents to answer this.",
            "citations": [],
            "status": "done",
        }

    prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
        objective=state["objective"],
        sources=sources_text,
    )
    answer = get_llm_provider().generate(prompt)

    return {**state, "final_answer": answer, "citations": citations, "status": "done"}
