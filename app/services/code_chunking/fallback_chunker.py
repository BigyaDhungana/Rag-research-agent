LINES_PER_CHUNK = 60
OVERLAP_LINES = 10


def chunk_naive(content: str) -> list[dict]:
    lines = content.splitlines()
    if not lines:
        return []

    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + LINES_PER_CHUNK, len(lines))
        chunk_lines = lines[start:end]
        chunks.append(
            {
                "content": "\n".join(chunk_lines),
                "start_line": start + 1,
                "end_line": end,
                "chunk_metadata": {
                    "symbol": None,
                    "node_type": "line_window",
                    "language": None,
                },
            }
        )
        if end == len(lines):
            break
        start = end - OVERLAP_LINES

    return chunks
