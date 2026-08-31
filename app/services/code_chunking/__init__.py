from app.services.code_chunking.ts_chunker import chunk_with_treesitter
from app.services.code_chunking.fallback_chunker import chunk_naive


def chunk_code_file(content: str, extension: str) -> list[dict]:
    ts_chunks = chunk_with_treesitter(content, extension)
    if ts_chunks is not None:
        return ts_chunks
    return chunk_naive(content)
