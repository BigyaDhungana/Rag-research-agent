def reciprocal_rank_fusion(candidates: list[dict], k: int = 60) -> list[dict]:
    """
    Combines vector_rank and keyword_rank into a single rrf_score per
    candidate. k=60 is the standard constant from the original RRF paper, 
    it dampens the impact of any single rank (especially rank 0) so one
    method doesn't dominate just because it happened to rank something #1.
    A candidate missing from one method (rank=None) simply contributes 0
    from that method.
    Returns list sorted by rrf_score descending.
    """
    for c in candidates:
        score = 0.0
        if c.get("vector_rank") is not None:
            score += 1.0 / (k + c["vector_rank"] + 1)
        if c.get("keyword_rank") is not None:
            score += 1.0 / (k + c["keyword_rank"] + 1)
        c["rrf_score"] = score

    return sorted(candidates, key=lambda c: c["rrf_score"], reverse=True)