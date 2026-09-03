JUDGE_PROMPT_TEMPLATE = """You are evaluating the quality of an AI-generated answer against the sources it was given. Score it on three dimensions, each 1-5 (5 = best).

Question: {question}

Sources provided to the AI:
{sources}

AI's generated answer:
{answer}

Score these three dimensions:
1. FAITHFULNESS (1-5): Does every claim in the answer trace back to something actually stated in the sources? 5 = fully grounded, no fabrication. 1 = mostly invented/unsupported claims.
2. RELEVANCE (1-5): Does the answer actually address the question asked? 5 = directly and completely answers it. 1 = off-topic or non-responsive.
3. CITATION_CORRECTNESS (1-5): Do the [Source N] citations in the answer actually point to sources that support the claim next to them? 5 = every citation is accurate. 1 = citations are wrong or missing where needed.

Respond with ONLY valid JSON, no other text:
{{"faithfulness": <int>, "relevance": <int>, "citation_correctness": <int>, "explanation": "<one sentence per dimension, brief>"}}
"""


def build_judge_prompt(question: str, sources: str, answer: str) -> str:
    return JUDGE_PROMPT_TEMPLATE.format(
        question=question, sources=sources, answer=answer
    )
