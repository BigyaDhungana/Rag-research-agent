# eval/metrics.py
def recall_at_k(retrieved: list[dict], is_relevant_fn, k: int) -> float:
    """1.0 if ANY of the top-k retrieved chunks are relevant, else 0.0.
    (Binary recall per-query since each eval example has one target passage so 
    not the multi-relevant-document recall formula.)"""
    top_k = retrieved[:k]
    return 1.0 if any(is_relevant_fn(r) for r in top_k) else 0.0


def precision_at_k(retrieved: list[dict], is_relevant_fn, k: int) -> float:
    """Fraction of the top-k that are relevant."""
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    relevant_count = sum(1 for r in top_k if is_relevant_fn(r))
    return relevant_count / len(top_k)


def reciprocal_rank(retrieved: list[dict], is_relevant_fn) -> float:
    """1/rank of the first relevant result found, 0 if none found."""
    for i, r in enumerate(retrieved, start=1):
        if is_relevant_fn(r):
            return 1.0 / i
    return 0.0
