from app.core.config import settings


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Web search via Tavily — purpose-built for LLM agents, so results come
    back as clean extracted content rather than raw SERP links.
    """
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(
        query=query,
        max_results=max_results,
        include_answer=False,
    )

    results = []
    for r in response.get("results", []):
        results.append(
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),  # Tavily's cleaned extract
                "score": r.get("score"),
                "source": "web",
            }
        )
    return results
