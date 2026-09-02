IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    "vendor",
    ".idea",
    ".vscode",
}

IGNORED_FILE_PATTERNS = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "composer.lock",
}

IGNORED_EXTENSIONS = {
    # binaries / media / archives
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".class",
    ".pyc",
    ".o",
    ".mp4",
    ".mp3",
    ".wav",
}

MAX_FILE_SIZE_BYTES = 1_000_000  # skip anything over 1MB


def should_ignore_dir(dirname: str) -> bool:
    return dirname in IGNORED_DIRS or dirname.startswith(".")


def should_ignore_file(filename: str, size_bytes: int) -> bool:
    if filename in IGNORED_FILE_PATTERNS:
        return True
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in IGNORED_EXTENSIONS:
        return True
    if size_bytes > MAX_FILE_SIZE_BYTES:
        return True
    return False
