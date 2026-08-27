from pypdf import PdfReader


def extract_text_by_page(file_path: str) -> list[dict]:
    reader = PdfReader(file_path)
    pages = []
    has_text = False
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            has_text = True
        pages.append({"page": i + 1, "text": text})

    if not has_text:
        raise ValueError(
            "This PDF appears to be scanned/images with no extractable text. OCR is not yet supported."
        )
    return pages
