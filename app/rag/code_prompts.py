CODE_QA_PROMPT_TEMPLATE = """You are a codebase assistant. Answer the question using ONLY the numbered code excerpts below, each labeled with its file path and line range.

Rules:
- Every claim must reference the specific file, function/symbol name, and line range it came from, e.g. "in `app/services/foo.py`, the `bar()` function (lines 12-30) does X".
- Cite using [Source N] after each claim, in addition to naming the file/function.
- If the excerpts don't contain enough information to answer, say so plainly rather than guessing at code you haven't seen.
- Do not invent file paths, function names, or line numbers not present in the sources.

Code excerpts:
{context}

Question: {question}

Answer:"""


def build_code_qa_prompt(question: str, context: str) -> str:
    return CODE_QA_PROMPT_TEMPLATE.format(context=context, question=question)
