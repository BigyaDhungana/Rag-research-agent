import os
from pathlib import Path

from app.services.repo_ingestion.ignore_rules import (
    should_ignore_dir,
    should_ignore_file,
)

# Extensions we actually want to treat as "code" for now  so kept explicit
# Everything ignred is not to be chunked 
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".swift",
    ".kt",
    ".scala",
    ".sql",
    ".sh",
    ".dart"
}


def discover_files(repo_path: Path) -> list[dict]:
    """
    Walks the cloned repo, applying dir and file ignore rules, returning
    only files with a recognized code extension. Returns relative paths
    (not absolute) since File.relative_path should survive the repo being
    re-cloned to a different local path later.
    """
    discovered = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]

        for filename in files:
            full_path = Path(root) / filename
            try:
                size = full_path.stat().st_size
            except OSError:
                continue

            if should_ignore_file(filename, size):
                continue

            ext = full_path.suffix.lower()
            if ext not in CODE_EXTENSIONS:
                continue

            discovered.append(
                {
                    "relative_path": str(full_path.relative_to(repo_path)),
                    "absolute_path": full_path,
                    "language": ext.lstrip("."),
                    "size_bytes": size,
                }
            )

    return discovered
