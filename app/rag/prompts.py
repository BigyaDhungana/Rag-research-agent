RAG_PROMPT_TEMPLATE = """You are a careful research assistant. Answer the question using ONLY the numbered sources below. Every claim in your answer must be traceable to a source.

Rules:
- Cite sources inline using [Source N] immediately after the claim they support.
- If the sources do not contain enough information to answer the question, respond EXACTLY with: "I don't have sufficient evidence in the provided documents to answer this question." Do not guess or use outside knowledge.
- Do not fabricate sources or citation numbers.

Sources:
{context}

Question: {question}

Answer:"""


def build_prompt(question: str, context: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(context=context, question=question)