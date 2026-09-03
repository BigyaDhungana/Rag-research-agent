import json
import random
import time
from pathlib import Path

from sqlalchemy.orm import Session

from eval.judge_prompt import build_judge_prompt
from app.rag.llm import get_llm_provider, LLMProviderError
from app.rag.context_builder import build_context
from app.services.hybrid_retrieval import retrieve
from app.services.rag_query import answer_query


def _extract_judge_json(raw: str) -> dict:
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```")[1].removeprefix("json").strip()
    return json.loads(stripped)


def run_generation_eval(
    db: Session,
    dataset_path: str,
    sample_size: int = 5,
    delay_between_examples: float = 2.0,
) -> dict:
    """
    Runs full generation (answer + judge) for a SAMPLE of eval questions.
    """
    examples = json.loads(Path(dataset_path).read_text())
    sample = random.sample(examples, min(sample_size, len(examples)))

    judge = get_llm_provider()
    results = []

    for i, ex in enumerate(sample):
        try:
            gen_result = answer_query(db, ex["question"])
            answer = gen_result["answer"]
            time.sleep(3)
            retrieval = retrieve(db, ex["question"])
            sources_text, _ = build_context(retrieval["results"])

            judge_prompt = build_judge_prompt(ex["question"], sources_text, answer)
            raw_judgment = judge.generate(judge_prompt)
            scores = _extract_judge_json(raw_judgment)

            results.append({"question": ex["question"], "answer": answer, **scores})

        except LLMProviderError as e:
            results.append(
                {
                    "question": ex["question"],
                    "answer": None,
                    "faithfulness": None,
                    "relevance": None,
                    "citation_correctness": None,
                    "explanation": f"LLM call failed, skipped: {e}",
                }
            )
        except (json.JSONDecodeError, IndexError):
            results.append(
                {
                    "question": ex["question"],
                    "answer": answer if "answer" in dir() else None,
                    "faithfulness": None,
                    "relevance": None,
                    "citation_correctness": None,
                    "explanation": "judge output unparseable",
                }
            )

        if i < len(sample) - 1:
            time.sleep(delay_between_examples)

    valid = [r for r in results if r["faithfulness"] is not None]
    n = len(valid)
    return {
        "n_scored": n,
        "n_failed_to_parse": len(results) - n,
        "mean_faithfulness": sum(r["faithfulness"] for r in valid) / n if n else None,
        "mean_relevance": sum(r["relevance"] for r in valid) / n if n else None,
        "mean_citation_correctness": (
            sum(r["citation_correctness"] for r in valid) / n if n else None
        ),
        "per_example": results,
    }
