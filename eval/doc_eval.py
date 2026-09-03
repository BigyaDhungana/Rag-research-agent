# eval/doc_eval.py
import json
from pathlib import Path

from sqlalchemy.orm import Session

from eval.metrics import recall_at_k, precision_at_k, reciprocal_rank
from app.services.hybrid_retrieval import retrieve


def _is_relevant_doc_chunk(chunk: dict, example: dict) -> bool:
    """
    Flexible match: content must contain ALL must_contain phrases
    (case-insensitive). Page no check not added yet
    """
    content_lower = chunk["content"].lower()
    return all(phrase.lower() in content_lower for phrase in example["must_contain"])


def run_doc_eval(db: Session, dataset_path: str, k: int = 5) -> dict:
    examples = json.loads(Path(dataset_path).read_text())

    results = []
    for ex in examples:
        retrieval = retrieve(db, ex["question"], final_k=k)
        retrieved = retrieval["results"]

        is_relevant = lambda chunk: _is_relevant_doc_chunk(chunk, ex)

        results.append(
            {
                "question": ex["question"],
                "source_document": ex["source_document"],
                "recall@k": recall_at_k(retrieved, is_relevant, k),
                "precision@k": precision_at_k(retrieved, is_relevant, k),
                "rr": reciprocal_rank(retrieved, is_relevant),
            }
        )

    n = len(results)
    summary = {
        "n_examples": n,
        "mean_recall@k": sum(r["recall@k"] for r in results) / n,
        "mean_precision@k": sum(r["precision@k"] for r in results) / n,
        "mrr": sum(r["rr"] for r in results) / n,
        "per_example": results,
    }
    return summary
