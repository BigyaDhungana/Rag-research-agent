from app.db.session import SessionLocal
from app.db.models.document import Document
from app.db.models.repository import Repository
from eval.doc_eval import run_doc_eval
from eval.code_eval import run_code_eval


def print_summary(name: str, summary: dict, label_key: str):
    print(f"\n=== {name} ===")
    print(f"n_examples: {summary['n_examples']}")
    print(f"Recall@k: {summary['mean_recall@k']:.3f}")
    print(f"Precision@k: {summary['mean_precision@k']:.3f}")
    print(f"MRR: {summary['mrr']:.3f}")
    for r in summary["per_example"]:
        status = "✓" if r["recall@k"] == 1.0 else "✗"
        print(f"  {status} [{r[label_key]}] {r['question'][:60]}")


def show_ingested_documents(db):
    docs = db.query(Document).all()
    print("=== Ingested documents ===")
    for d in docs:
        print(f"  {d.filename:40s} status={d.status}")
    print()


def show_ingested_repos(db):
    repos = db.query(Repository).all()
    print("=== Ingested repositories ===")
    for r in repos:
        print(f"  {str(r.id)}  {r.name:40s} status={r.status}")
    print()
    return repos


if __name__ == "__main__":
    db = SessionLocal()

    show_ingested_documents(db)
    repos = show_ingested_repos(db)

    doc_summary = run_doc_eval(db, "eval/data/doc_eval.json", k=5)
    print_summary("Document Retrieval Eval", doc_summary, "source_document")

    REPO1_ID = "1eede4f1-b836-42ad-bfbd-37543ac10660"
    REPO2_ID = "67f34781-faad-4113-9433-b2207ee18782"

    if REPO1_ID:
        r1 = run_code_eval(db, REPO1_ID, "eval/data/repo1_eval.json", k=5)
        print_summary("Code Eval — Repo 1", r1, "source_file")
    else:
        print("\n[Skipped Repo 1 eval — set REPO1_ID at the top of run_eval.py]")

    if REPO2_ID:
        r2 = run_code_eval(db, REPO2_ID, "eval/data/repo2_eval.json", k=5)
        print_summary("Code Eval — Repo 2", r2, "source_file")
    else:
        print("\n[Skipped Repo 2 eval — set REPO2_ID at the top of run_eval.py]")

    db.close()
