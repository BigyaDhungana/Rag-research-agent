# eval/code_eval.py
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.code_retrieval import retrieve_code


def _is_relevant_code_chunk(chunk: dict, example: dict) -> bool:
    """
    Requires must_contain AND at least one of (file match, symbol match)
    as corroboration; must_contain alone can occasionally false-positive
    on generic phrases; requiring the file or symbol to also line up
    makes the check meaningfully stricter without demanding both (since
    either path-nesting or symbol-metadata assumptions could be slightly
    off without the retrieval actually being wrong).
    """
    content_lower = chunk["content"].lower()
    if not all(phrase.lower() in content_lower for phrase in example["must_contain"]):
        return False

    file_ok = chunk["file_path"].endswith(example["source_file"]) or example[
        "source_file"
    ].endswith(chunk["file_path"])

    expected_symbol = example["expected_symbol"]
    actual_symbol = chunk.get("symbol") or ""
    parent = chunk.get("parent_class")
    combined = f"{parent}.{actual_symbol}" if parent else actual_symbol
    symbol_ok = expected_symbol in (actual_symbol, combined)

    return file_ok or symbol_ok


def run_code_eval(
    db: Session, repository_id: str, dataset_path: str, k: int = 5
) -> dict:
    examples = json.loads(Path(dataset_path).read_text())

    results = []
    for ex in examples:
        retrieval = retrieve_code(db, repository_id, ex["question"], final_k=k)
        retrieved = retrieval["results"]

        from eval.metrics import recall_at_k, precision_at_k, reciprocal_rank

        is_relevant = lambda chunk: _is_relevant_code_chunk(chunk, ex)

        results.append(
            {
                "question": ex["question"],
                "source_file": ex["source_file"],
                "recall@k": recall_at_k(retrieved, is_relevant, k),
                "precision@k": precision_at_k(retrieved, is_relevant, k),
                "rr": reciprocal_rank(retrieved, is_relevant),
            }
        )

    n = len(results)
    return {
        "n_examples": n,
        "mean_recall@k": sum(r["recall@k"] for r in results) / n,
        "mean_precision@k": sum(r["precision@k"] for r in results) / n,
        "mrr": sum(r["rr"] for r in results) / n,
        "per_example": results,
    }
