from sqlalchemy.orm import Session

from app.db.models.repository import Repository, RepositoryStatus, File
from app.services.repo_ingestion.clone import (
    clone_repository,
    derive_repo_name,
    CloneError,
)
from app.services.repo_ingestion.discovery import discover_files


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

        repo.status = RepositoryStatus.ready
        db.commit()

    except CloneError as e:
        repo.status = RepositoryStatus.failed
        repo.error_message = str(e)
        db.commit()

    db.refresh(repo)
    return repo
