from abc import ABC, abstractmethod


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """Return the top_k candidates, ordered best-first, with a rerank_score set."""
        raise NotImplementedError


class CrossEncoderReranker(Reranker):
    """
    Local cross-encoder reranker via sentence-transformers. 
    Runs on the ~20 survivors of RRF, not the whole corpus.
    """

    _MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(self._MODEL_NAME)

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        if not candidates:
            return []

        pairs = [(query, c["content"]) for c in candidates]
        scores = self._model.predict(pairs)

        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)

        ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
        return ranked[:top_k]


_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    return _reranker
