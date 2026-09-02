from sqlalchemy.orm import Session

from app.db.models.repository import Repository, RepositoryStatus, File
from app.services.repo_ingestion.clone import (
    clone_repository,
    derive_repo_name,
    CloneError,
)
from app.services.repo_ingestion.discovery import discover_files
from app.services.code_processor import process_repository_files


def ingest_repository(db: Session, url: str) -> Repository:
    repo = Repository(
        url=url,
        name=derive_repo_name(url),
        local_path="",  # filled in once clone succeeds
        status=RepositoryStatus.cloning,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    try:
        repo_id, local_path = clone_repository(url)
        repo.local_path = str(local_path)
        repo.status = RepositoryStatus.processing
        db.commit()

        discovered = discover_files(local_path)
        for f in discovered:
            db.add(
                File(
                    repository_id=repo.id,
                    relative_path=f["relative_path"],
                    language=f["language"],
                    size_bytes=f["size_bytes"],
                )
            )
        db.commit()
        db.refresh(repo)  # ensures repo.files has real ids before chunking

    except CloneError as e:
        repo.status = RepositoryStatus.failed
        repo.error_message = str(e)
        db.commit()
        db.refresh(repo)
        return repo

    try:
        process_repository_files(db, repo.local_path, repo.files)
        repo.status = RepositoryStatus.ready
        db.commit()

    except Exception as e:
        # Chunking/embedding failure (bad file, tree-sitter crash,
        # embedding call error), so the repo doesn't get stuck at "processing" forever with no reason why.
        db.rollback()
        repo.status = RepositoryStatus.failed
        repo.error_message = f"Chunking/embedding failed: {e}"
        db.commit()

    db.refresh(repo)
    return repo
