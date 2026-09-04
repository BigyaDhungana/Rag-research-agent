# RAG Research Agent

An AI platform that combines document retrieval-augmented generation (RAG), a tool-using research agent, and codebase-aware RAG into a single FastAPI service. It's designed around one core idea: retrieval quality matters more than model choice, so every feature is built on a shared, carefully-tuned retrieval pipeline rather than leaning on a single large model to compensate for weak search.

## What it does

**Document RAG.** Upload PDFs and ask natural-language questions answered directly from their content. Every answer comes with inline citations pointing back to the specific source passage, and the system explicitly refuses to answer when the uploaded documents don't contain enough evidence, rather than guessing.

**Research Agent.** Give it an open-ended objective, a question that might need current web information, your own documents, or both and it plans a sequence of steps, decides which tools each step needs, executes them, and synthesizes a single answer that cites both web and document sources where both were used. The planner doesn't guess blindly at whether your documents are relevant: it runs a lightweight pre-check against what's actually uploaded before deciding whether a document search step is worth including.

**Codebase RAG.** Point it at a public GitHub repository and ask real questions about the code — "how does X work," "where is Y handled." Code is parsed into functions, methods, and classes as individual chunks (not arbitrary line-count windows), so answers reference actual file paths, function/method names, and line numbers, letting you jump straight to the relevant code rather than reading a paraphrase of it.

## How retrieval works

Every feature shares the same retrieval core: a query is rewritten to strip filler phrasing, then searched two ways in parallel — dense vector similarity and Postgres full-text keyword search — and the two candidate sets are merged with Reciprocal Rank Fusion, which combines rankings from both methods without needing to normalize incompatible similarity scores. The fused candidates are then reranked with a cross-encoder, which scores each (query, passage) pair jointly rather than relying on precomputed embedding similarity, giving a meaningfully more accurate final ordering before the top results are handed to an LLM for generation.

## Orchestration

The research agent is built as a LangGraph state machine: a planner produces a structured, validated plan; a tool router executes each step against a fixed, explicit tool registry (no arbitrary code execution); and a synthesizer combines whatever evidence was gathered — including gracefully handling individual tool failures without aborting the whole run — into a final cited answer.

## Architecture

### Data flow

Documents and repositories go through the same conceptual pipeline before anything can be queried: content is extracted, split into chunks, embedded, and stored alongside a full-text index. Documents are extracted with PyMuPDF and split with a character-based sliding window. Repositories are cloned locally, walked with language/size/pattern ignore rules (skipping `.git`, `node_modules`, lockfiles, binaries, and anything over 1MB), and parsed with tree-sitter into function-, method-, and class-level chunks rather than arbitrary line windows — a class produces one header chunk plus a separate chunk per method, so retrieval can return a single relevant method instead of an entire file.

### Retrieval pipeline

A query is first rewritten to strip conversational filler ("what is," "how do I," trailing punctuation), then run through two independent searches: dense vector similarity over embeddings, and Postgres full-text keyword search via a GIN-indexed `tsvector`. Both candidate sets are merged and deduplicated, then combined with Reciprocal Rank Fusion (RRF), which fuses two differently-scaled ranking signals into one ordering without needing score normalization. The fused top-N candidates are reranked with a cross-encoder — a model that scores each (query, passage) pair jointly, which is slower per-pair than embedding similarity but meaningfully more accurate at judging relevance — and the final top-K are handed to an LLM along with a prompt that requires inline citations and explicitly permits "insufficient evidence" as a valid answer.

### Research agent

The research agent is a LangGraph state machine with three node types. A planner calls an LLM to produce a structured, schema-validated plan — a sequence of steps, each tagged with exactly one tool (`search_web`, `search_documents`, or `fetch_page`) and a reason. Critically, the planner isn't guessing about document relevance from the objective's wording alone: before planning, a cheap keyword+vector pre-check runs against the actual document store, and its result — including a real content snippet if something matched — is injected into the planner's prompt as evidence. A tool router then executes each step in sequence against a fixed tool registry; execution is restricted to registered tools only, and any individual tool failure (a web search timeout, for example) is captured per-step without halting the run, so the agent still synthesizes an answer from whatever evidence succeeded. A synthesizer combines all gathered evidence — labeling each source as web or document — into one final answer with per-source citations, and is explicitly instructed to flag when sources with similar names likely refer to different entities rather than merging them.

### Codebase RAG

Repository ingestion clones a public GitHub repo, discovers source files under a language allowlist, and parses each file with tree-sitter (currently configured for Python and Dart, with a naive line-window fallback for any other language or on a parse failure). Class bodies are recursed into: each method becomes its own chunk tagged with its parent class and symbol name, rather than the whole class being treated as one large indivisible unit. The same hybrid-search-plus-rerank pipeline used for documents is reused here, scoped to a single repository, and the generation prompt requires every claim to reference a specific file path, symbol name, and line range.

### Observability

Every request through the RAG, code-QA, and research-agent pipelines is traced end-to-end with Langfuse: retrieval, reranking, and generation each appear as nested spans under a single request trace, with real token usage reported for cost tracking and full input/output visible per step.

## Features

### Document RAG

Upload PDF documents and query them directly. The system extracts text, chunks it, embeds each chunk locally, and stores it alongside a full-text index. Queries go through the full hybrid-search-plus-rerank pipeline, and the top results are passed to an LLM with a prompt requiring inline `[Source N]` citations for every claim. If the retrieved content genuinely doesn't answer the question, the model is instructed to say so explicitly rather than fabricate an answer — citations are only returned when the answer is actually grounded.

### Research Agent

Give the agent a single open-ended objective and it handles the rest: planning which tools are needed, executing them, and synthesizing one final answer. The planner produces a structured, schema-validated JSON plan — a sequence of steps, each using exactly one of three tools:

- `search_web` — searches the public web via Tavily, returning cleaned page content rather than raw search-engine links
- `search_documents` — searches your own uploaded documents through the same retrieval pipeline used by Document RAG
- `fetch_page` — fetches and extracts the full content of a specific URL, only used when a step already has a concrete URL to follow, never invented

The planner grounds its tool choices in reality rather than guessing from the objective's wording alone — it runs a cheap pre-check against the document store before deciding whether a document-search step is warranted, so it doesn't skip a relevant document search just because the objective happens to also sound like a general web lookup. Once steps execute, a synthesizer combines all gathered evidence into a single answer, labeling and citing each source as web or document, and explicitly calling out when sources with similar names appear to refer to different people or entities rather than merging them into one profile.

### Codebase RAG

Point the system at a public GitHub repository and it clones it, discovers source files, and parses them into meaningful units — functions, methods, and classes — rather than splitting by line count. Each method is chunked individually and tagged with its parent class and symbol name, so a search for "how does X work" can return exactly the relevant method instead of an entire file. Two endpoints are available: one returns raw ranked code chunks with file path, symbol, and line numbers (no LLM involved), and the other generates a full natural-language answer with citations pointing to specific files, functions, and line ranges.

### Shared retrieval quality

All three features are built on the same retrieval core rather than three separate implementations: hybrid vector + keyword search, Reciprocal Rank Fusion, and cross-encoder reranking. This was a deliberate architectural choice — improving retrieval quality once benefits every feature built on top of it, rather than needing three separate tuning efforts.

### Observability

Every request is traced end-to-end through Langfuse — retrieval, reranking, and generation each show up as nested spans under one request trace, with real token usage and latency visible per step, making it possible to inspect exactly what a query retrieved and what the model was actually shown before generating its answer.

## Tech Stack

**API framework:** FastAPI, running on Uvicorn.

**Database:** PostgreSQL with the `pgvector` extension for vector similarity search, plus native full-text search (`tsvector`/GIN indexes) for keyword retrieval. Schema managed via SQLAlchemy models and Alembic migrations.

**Embeddings:** Local, via `sentence-transformers` (`all-MiniLM-L6-v2`), so embedding generation doesn't depend on an external API.

**Reranking:** A local cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`, also via `sentence-transformers`) scores query-passage pairs jointly for the final ranking stage.

**LLM:** Google Gemini, via the `google-genai` SDK, used for the planner, synthesizer, RAG/code-QA generation, and the generation-quality eval judge.

**Web search:** Tavily, used by the research agent's `search_web` tool, returning cleaned extracted content rather than raw search-engine results.

**Page fetching:** `httpx` for the HTTP request and `trafilatura` for extracting clean article text from arbitrary URLs, used by the `fetch_page` tool.

**Agent orchestration:** LangGraph, structuring the research agent as an explicit state machine (planner → tool router → synthesizer) with a typed `AgentState` passed between nodes.

**Code parsing:** `tree-sitter-language-pack`, parsing source files into real ASTs so code chunking is based on actual function/method/class boundaries rather than line counts.

**PDF extraction:** PyMuPDF (`fitz`), extracting text per page from uploaded documents.

**Observability:** Langfuse, tracing every pipeline end-to-end with nested spans and per-call token usage.

**Containerization:** Docker and Docker Compose, running the API and PostgreSQL as separate services with automatic migrations on container start.

## Setup / Quickstart

### Prerequisites

- Docker and Docker Compose
- API keys for Gemini, Tavily, and Langfus — see `.env.example` for what's required and where to get each one

### Steps

1. Clone the repository:

```bash
   git clone https://github.com/BigyaDhungana/Rag-research-agent.git
   cd Rag-research-agent
```

2. Copy the environment template and fill in your API keys:

```bash
   cp .env.example .env
```

3. Make the startup script executable, then run it:

```bash
   chmod +x run.sh
   ./run.sh
```

This builds the images, starts PostgreSQL and the API, and runs database migrations automatically before the API starts serving — no manual migration step needed on a fresh setup.

4. Confirm it's running:

```bash
   curl http://localhost:8000/health
```

Interactive API docs (Swagger UI) are available at `http://localhost:8000/docs`.

### Platform notes

This project is developed and tested on Linux/macOS. On Windows, use Docker Desktop with the WSL2 backend (the default in recent versions) and run `run.sh` from a WSL2 terminal or Git Bash — the script relies on POSIX shell commands (`id -u`, `id -g`) that aren't available in PowerShell or `cmd.exe`.

### Everyday development

Code changes are picked up automatically — the API container runs with `--reload` and the project directory is bind-mounted, so editing a Python file takes effect without restarting or rebuilding anything. A rebuild (`./run.sh` again, which always passes `--build`) is only actually necessary when `requirements.txt` or the Dockerfile changes; Docker's layer caching means this is fast in every other case, since only the layers that changed re-run.

## API Reference

Interactive documentation with request/response schemas is available at `/docs` once the service is running. This section covers the core endpoints by feature area. All routes are prefixed with `/api/v1` except `/health`.

### Health

```bash
curl -X POST http://localhost:8000/health
```

Returns `{"status": "ok"}`. No auth, no dependencies checked — a liveness check, not a readiness check.

### Documents

**Upload a document**

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@/path/to/document.pdf"
```

**Search — vector similarity only**

```bash
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here", "top_k": 5}'
```

**Search — hybrid (vector + keyword), no reranking**

```bash
curl -X POST http://localhost:8000/api/v1/documents/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here", "top_k": 5}'
```

**Search — full pipeline (hybrid + RRF + cross-encoder rerank)**

```bash
curl -X POST http://localhost:8000/api/v1/documents/search/rerank \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here"}'
```

### RAG Query

**Ask a question, get a cited, generated answer**

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "your question here"}'
```

Response includes the generated `answer`, a `citations` list (chunk/document/page references), and `used_documents` indicating whether the answer was actually grounded or fell back to an insufficient-evidence response.

### Research Agent

Both agent endpoints take `objective` as a **query parameter**, not a JSON body.

**Plan only (debug — no execution)**

```bash
curl -X POST "http://localhost:8000/api/v1/agent/plan?objective=your+objective+here"
```

**Full run (plan, execute, synthesize)**

```bash
curl -X POST "http://localhost:8000/api/v1/agent/research?objective=your+objective+here"
```

Response includes the `plan`, per-step `tool_results`, the synthesized `answer`, `citations` (each tagged with which tool it came from), and the run's final `status`.

### Repositories (Codebase RAG)

**Ingest a public repository**

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/owner/repo"}'
```

Returns a `repository_id`, used in the two endpoints below. Ingestion clones, discovers files, chunks, and embeds synchronously — the response only returns once processing finishes (or fails).

**Search code — raw ranked chunks, no generation**

```bash
curl -X POST http://localhost:8000/api/v1/repositories/{repository_id}/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here", "top_k": 5}'
```

**Ask a question about the codebase — generated, cited answer**

```bash
curl -X POST http://localhost:8000/api/v1/repositories/{repository_id}/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "your question here"}'
```

Response citations reference file path, symbol name, parent class (if applicable), and line range for each source used.

## Project Structure

```
.
├── app/
│   ├── agent/              # Research agent: planner, tool router, synthesizer, LangGraph state
│   │   ├── nodes/           # Individual graph nodes (planner_node, tool_router, synthesizer)
│   │   └── tools/           # Agent tools: search_web, search_documents, fetch_page
│   ├── api/
│   │   ├── health.py        # GET /health
│   │   └── v1/               # All /api/v1 routers: document, rag, agent, repository
│   ├── core/                # Settings, storage config
│   ├── db/
│   │   ├── models/           # SQLAlchemy models (Document, DocumentChunk, Repository, File, CodeChunk)
│   │   └── session.py
│   ├── observability/       # Langfuse client
│   ├── rag/                 # Core retrieval/generation primitives shared across features
│   │   ├── embeddings.py     # Local sentence-transformers embedding provider
│   │   ├── llm.py            # Gemini LLM provider, retry/error handling
│   │   ├── query_rewriter.py
│   │   ├── rrf.py            # Reciprocal Rank Fusion
│   │   ├── reranker.py       # Cross-encoder reranker
│   │   ├── prompts.py / code_prompts.py
│   │   └── context_builder.py
│   ├── schemas/              # Pydantic request/response models
│   └── services/
│       ├── document_processor.py / document_search.py / document_service.py
│       ├── keyword_search.py / hybrid_retrieval.py / rag_query.py
│       ├── pdf_extractor.py
│       ├── code_chunking/    # Tree-sitter chunker + language config + naive fallback
│       ├── code_search.py / code_keyword_search.py / code_retrieval.py / code_qa.py
│       ├── code_processor.py
│       └── repo_ingestion/   # Repo cloning, file discovery, ignore rules
├── alembic/                 # Database migrations
├── eval/
│   ├── data/                 # Eval datasets (doc + code question/answer ground truth)
│   ├── doc_eval.py / code_eval.py / metrics.py
│   ├── generation_eval.py / judge_prompt.py    # LLM-as-judge generation quality eval
│   ├── agent_qualitative_check.py
│   └── run_eval.py           # Single entry point running all evals
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh             # Runs migrations, then starts uvicorn
├── run.sh                    # Wraps docker compose up with correct UID/GID
├── requirements.txt
└── .env.example
```

## Evaluation

A retrieval and generation evaluation suite lives under `eval/`, run via a single entry point:

```bash
docker compose exec -T api python3 -m eval.run_eval
```

### Retrieval metrics

Retrieval quality is measured with Recall@K, Precision@K, and Mean Reciprocal Rank (MRR), against a hand-authored dataset of question/ground-truth pairs — 40 questions across 6 documents, and 20 questions across 2 code repositories. Ground truth is expressed as required keyword phrases that must appear in a retrieved chunk, rather than exact chunk IDs, so the dataset stays valid across re-ingestion.

|                    | Recall@5  | Precision@5 | MRR        |
| ------------------ | --------- | ----------- | ---------- |
| Document retrieval | 0.450     | ~0.10       | 0.450      |
| Code retrieval     | 0.70–0.80 | ~0.14       | ~0.60–0.63 |

Precision@5 is low by construction, not by defect: each question has exactly one relevant passage, so the best possible precision on a correct hit at k=5 is 0.2, not 1.0.

### Generation quality

Generated answers are scored on faithfulness, relevance, and citation correctness using an LLM-as-judge approach — a sampled subset of the document eval questions is run through the full generation pipeline, and the same model class scores the resulting answer against the sources it was given.

| Metric               | Mean score (out of 5) |
| -------------------- | --------------------- |
| Faithfulness         | 5.00                  |
| Relevance            | 4.93                  |
| Citation correctness | 5.00                  |

**Caveat:** the same model is used for both generation and judging in this eval. This is a known limitation of LLM-as-judge setups — a model can be systematically blind to its own failure patterns or rate its own outputs favorably, and scores this consistent should be read as a rough internal signal rather than independent verification. See Future Enhancements for the plan to use an independent judge model.

### Research agent qualitative check

The research agent's tool selection isn't scored against Recall@K/MRR, since web search results aren't stable or reproducible across runs the way documents and code are. Instead, a small set of objectives — each deliberately requiring both web and document evidence — is checked structurally: did the planner choose to use both tool types, and did the final answer actually cite both. All tested objectives passed this check.

## Known Limitations

**Synchronous processing.** Document and repository ingestion (extract, chunk, embed) run inline within the request — there's no background job queue. This is fine at current scale, but large files or repositories could make upload latency a real problem; a Celery/Redis-based worker would be the natural next step if that happens.

**Public repositories only.** Repository ingestion clones over HTTPS with no authentication support, so private repositories can't be ingested. Attempting one fails cleanly with a clear git error rather than hanging, but there's no token/SSH auth path yet.

**JS/TypeScript code chunking is unverified.** Tree-sitter-based code chunking has been tested and confirmed correct against real repositories for Python and Dart, including edge cases like named and factory constructors. JavaScript/TypeScript configuration exists but has not been tested against a real repository, and should not be trusted without verification first.

**Undiagnosed retrieval gap on some documents.** Three of the six documents in the evaluation set score meaningfully below the others on Recall@5. This has been confirmed not to be a text-extraction problem — the underlying extracted text is clean on all three — but the actual cause hasn't been identified. Candidates include chunk-boundary splitting cutting relevant passages awkwardly, or ground-truth phrases that paraphrase rather than exactly match the source text.

**LLM-as-judge uses the same model as generation.** The generation-quality evaluation (faithfulness, relevance, citation correctness) is scored by the same model that generated the answers being judged, which is a known bias risk in LLM-as-judge setups. Scores should be treated as a rough internal signal, not independent verification.


**Not production-hardened.** The current setup is oriented toward local development: the API runs with auto-reload enabled, the project directory is fully bind-mounted into the container, and there's no multi-worker process manager, TLS termination, or separate production build stage.

## Future Enhancements

**Independent LLM-as-judge.** Configure a dedicated evaluator — either Langfuse's built-in judge templates (Hallucination, Relevance, Helpfulness, Context Relevance/Correctness), which can score traces automatically or be backfilled onto historical ones, or a custom judge — using a model different from the one used for generation, to remove the self-judging bias currently present in the generation-quality eval.

**Private repository support.** Add token or SSH-based authentication for `git clone`, so repository ingestion isn't limited to public repositories.

**JS/TypeScript chunking verification.** Confirm the existing tree-sitter configuration for JavaScript/TypeScript against a real repository, the same way Python and Dart were verified, before relying on its chunking quality.

**Background job queue.** Move document and repository ingestion to Celery/Redis-backed background workers, so large files or repositories don't block the request while processing.

**Deeper nested-symbol chunking.** Code chunking currently handles one level of class-to-method nesting. A function or class defined nested inside another function or class isn't separately chunked — extending this would improve retrieval granularity for more deeply nested code.

**Stored full-text search column.** Full-text search currently uses a functional index computed on the fly from `content`. A stored, trigger-maintained `tsvector` column would be cheaper to query at larger scale, at the cost of needing a migration and trigger to keep it in sync.


