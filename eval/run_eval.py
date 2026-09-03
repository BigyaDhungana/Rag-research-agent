from app.db.session import SessionLocal
from app.db.models.document import Document
from app.db.models.repository import Repository
from eval.doc_eval import run_doc_eval
from eval.code_eval import run_code_eval
from eval.agent_qualitative_check import run_qualitative_check
from eval.generation_eval import run_generation_eval


def print_retrieval_summary(name: str, summary: dict, label_key: str):
    print(f"\n=== {name} ===")
    print(f"n_examples: {summary['n_examples']}")
    print(f"Recall@k: {summary['mean_recall@k']:.3f}")
    print(f"Precision@k: {summary['mean_precision@k']:.3f}")
    print(f"MRR: {summary['mrr']:.3f}")
    for r in summary["per_example"]:
        status = "✓" if r["recall@k"] == 1.0 else "✗"
        print(f"  {status} [{r[label_key]}] {r['question'][:60]}")


def print_generation_summary(summary: dict):
    print("\n=== Generation Quality Eval (LLM-as-judge) ===")
    print(
        "CAVEAT: the SAME model (Gemini) is used for both generation AND "
        "judging in this eval. This is a known self-judging bias risk — a "
        "model can be systematically blind to its own failure patterns or "
        "rate its own outputs favorably. Treat these scores as a rough "
        "internal signal, not independent verification. See PROGRESS.md "
        "Future Enhancements for the plan to use a separate judge model."
    )
    print(
        f"n_scored: {summary['n_scored']}  (n_failed_to_parse: {summary['n_failed_to_parse']})"
    )
    if summary["n_scored"]:
        print(f"Mean faithfulness: {summary['mean_faithfulness']:.2f}/5")
        print(f"Mean relevance: {summary['mean_relevance']:.2f}/5")
        print(
            f"Mean citation_correctness: {summary['mean_citation_correctness']:.2f}/5"
        )
    for r in summary["per_example"]:
        print(f"\n  Q: {r['question'][:70]}")
        print(
            f"  Scores: faithfulness={r.get('faithfulness')}, relevance={r.get('relevance')}, citation_correctness={r.get('citation_correctness')}"
        )
        if r.get("explanation"):
            print(f"  Explanation: {r['explanation']}")


def print_qualitative_summary(results: list[dict]):
    print("\n=== Research Agent — Qualitative Check ===")
    print(
        "NOTE: not a scored retrieval metric — web results aren't stable/"
        "reproducible enough for Recall@K/MRR to mean anything here. This "
        "is a structural pass/fail check: did the agent choose to use both "
        "tools when the objective called for both, and did it cite both."
    )
    for r in results:
        both = "✓" if r["used_both_tool_types"] else "✗ (only one tool type used)"
        print(f"\n  Objective: {r['objective']}")
        print(f"  Status: {r['status']}")
        print(f"  Tools planned: {r['tools_planned']}")
        print(f"  Citation sources used: {r['citation_tools_used']}")
        print(f"  Used both tool types: {both}")
        print(f"  Answer preview: {r['answer_preview']}")


def show_ingested_documents(db):
    docs = db.query(Document).all()
    print("=== Ingested documents ===")
    for d in docs:
        print(f"  {d.filename:45s} status={d.status}")
    print()


def show_ingested_repos(db):
    repos = db.query(Repository).all()
    print("=== Ingested repositories ===")
    for r in repos:
        print(f"  {str(r.id)}  {r.name:40s} status={r.status}")
    print()


if __name__ == "__main__":
    db = SessionLocal()

    show_ingested_documents(db)
    show_ingested_repos(db)

    doc_summary = run_doc_eval(db, "eval/data/doc_eval.json", k=5)
    print_retrieval_summary("Document Retrieval Eval", doc_summary, "source_document")

    REPO1_ID = "1eede4f1-b836-42ad-bfbd-37543ac10660"
    REPO2_ID = "67f34781-faad-4113-9433-b2207ee18782"

    if REPO1_ID:
        r1 = run_code_eval(db, REPO1_ID, "eval/data/repo1_eval.json", k=5)
        print_retrieval_summary("Code Eval — Repo 1", r1, "source_file")
    else:
        print("\n[Skipped Repo 1 eval — set REPO1_ID at the top of run_eval.py]")

    if REPO2_ID:
        r2 = run_code_eval(db, REPO2_ID, "eval/data/repo2_eval.json", k=5)
        print_retrieval_summary("Code Eval — Repo 2", r2, "source_file")
    else:
        print("\n[Skipped Repo 2 eval — set REPO2_ID at the top of run_eval.py]")

    gen_summary = run_generation_eval(db, "eval/data/doc_eval.json", sample_size=5)
    print_generation_summary(gen_summary)

    qualitative_results = run_qualitative_check(db)
    print_qualitative_summary(qualitative_results)

    db.close()
