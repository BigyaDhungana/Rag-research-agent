import subprocess
import os
import uuid
from pathlib import Path

STORAGE_ROOT = Path("storage/repositories")


class CloneError(Exception):
    pass


def clone_repository(url: str) -> tuple[str, Path]:
    """
    Shells out to `git clone`
    """
    repo_id = str(uuid.uuid4())
    dest = STORAGE_ROOT / repo_id
    dest.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        raise CloneError(f"git clone failed: {e.stderr}") from e
    except subprocess.TimeoutExpired as e:
        raise CloneError(f"git clone timed out after 120s: {e}") from e

    return repo_id, dest


def derive_repo_name(url: str) -> str:
    """e.g. https://github.com/owner/repo(.git) -> 'owner/repo'"""
    cleaned = url.rstrip("/").removesuffix(".git")
    parts = cleaned.split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else cleaned
