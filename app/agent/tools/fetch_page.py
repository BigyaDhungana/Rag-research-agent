import httpx
from trafilatura import extract
from urllib.parse import urlparse


def fetch_page(url: str, timeout: float = 10.0) -> dict:
    """
    Fetches a single URL and extracts clean article text.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return {
            "url": url,
            "content": None,
            "error": "invalid URL format",
            "source": "web",
        }
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (research-agent)"},
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        return {"url": url, "content": None, "error": str(e), "source": "web"}

    text = extract(response.text, include_comments=False, include_tables=True)

    if not text:
        return {
            "url": url,
            "content": None,
            "error": "no extractable content",
            "source": "web",
        }

    return {"url": url, "content": text, "error": None, "source": "web"}
