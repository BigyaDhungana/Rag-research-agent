import fitz


def extract_text_by_page(file_path: str) -> list[dict]:
    """
    "text" mode extraction (page.get_text()) is used rather than the
    richer "blocks"/"dict" modes — this preserves the existing contract
    (plain text per page) so chunking and everything downstream needs
    no changes.
    """
    doc = fitz.open(file_path)
    pages = []
    has_text = False

    for i, page in enumerate(doc):
        text = page.get_text() or ""
        if text.strip():
            has_text = True
        pages.append({"page": i + 1, "text": text})

    doc.close()

    if not has_text:
        raise ValueError(
            "This PDF appears to be scanned/images with no extractable text. OCR is not yet supported."
        )
    return pages
