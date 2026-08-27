from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(pages: list[dict], chunk_size=1000, chunk_overlap=150) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],  # Respects paragraphs first
        length_function=len,
    )

    chunks = []
    chunk_index = 0
    for page in pages:
        text = page["text"]
        if not text.strip():
            continue
        # Split the page text into semantic chunks
        chunk_texts = splitter.split_text(text)
        for content in chunk_texts:
            if content.strip():
                chunks.append(
                    {
                        "content": content.strip(),
                        "page_number": page["page"],
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1
    return chunks
