from abc import ABC, abstractmethod


class QueryRewriter(ABC):

    @abstractmethod
    def rewrite(self, query: str) -> str:
        """Return a cleaned/normalized version of the query for retrieval."""
        raise NotImplementedError


class SimpleQueryRewriter(QueryRewriter):
    """
    Rule-based rewriter: no LLM call
    - Strips/collapses whitespace
    - Drops common filler prefixes people type into search boxes
      ("what is", "how do i", "explain", etc.)
    Deliberately does NOT do stopword removal on the whole query, Postgres's
    own plainto_tsquery already handles stemming/stopwords
    """

    _FILLER_PREFIXES = (
        "what is ",
        "what are ",
        "how do i ",
        "how does ",
        "how to ",
        "can you tell me about ",
        "tell me about ",
        "explain ",
    )
    _TRAILING_PUNCTUATION = "?.!,;:"

    def rewrite(self, query: str) -> str:
        cleaned = " ".join(query.strip().split())
        lowered = cleaned.lower()
        for prefix in self._FILLER_PREFIXES:
            if lowered.startswith(prefix):
                cleaned = cleaned[len(prefix) :]
                break
        cleaned = cleaned.strip().rstrip(self._TRAILING_PUNCTUATION).strip()
        return cleaned or query.strip()


_provider: QueryRewriter | None = None


def get_query_rewriter() -> QueryRewriter:
    global _provider
    if _provider is None:
        _provider = SimpleQueryRewriter()
    return _provider
