import os
import uuid

UPLOAD_DIR = "storage/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_file(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1]
    stored_name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(content)
    return path
