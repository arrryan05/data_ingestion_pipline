# Data Ingestion Pipeline

This repository implements a **Temporally‑orchestrated**, **async** Python ingestion pipeline that:

1. **Downloads** documents from arbitrary URLs.  
2. **Parses** them into text chunks (PDF, DOCX, DOC, XLSX, XLS).  
3. **Embeds** each chunk using Cohere’s embedding API.  
4. **Stores** the chunks in a ChromaDB collection for downstream retrieval.

It uses:

- **Temporal.io** (via the Temporal Python SDK) for workflow orchestration, retries, and state.  
- **asyncio** inside each Activity for non‑blocking I/O.  
- **Cohere** for text embeddings.  
- **ChromaDB**  as the vector store.  

---

## Architecture

```text
┌───────────────┐       ┌─────────────┐     ┌─────────────┐
│  trigger CLI  ├─►│ Temporal Frontend ├─► ─┤  Workflow   │
└───────────────┘       └─────────────┘     │ Activities  │
                                            └─────────────┘
    |                                              │     ├─ fetch_document
    ▼                                              │     ├─ parse_document
(workflow run)                                     │     ├─ generate_embedding
    │                                              │     └─ store_chunk
    ▼                                              ▼
┌───────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Cohere Embed  │    │ ChromaDB     │    │ Local Temp Files│
└───────────────┘    └──────────────┘    └─────────────────┘

```
## Steps to Run
- run `docker-compose up --build -d`   
- open worker logs with `docker-compose logs -f worker`
- In another terminal run `docker-compose exec worker bash` to start a bash terminal inside the worker
- Run a input in following format `python src/run_ingest.py --file-id example123 --file-url https://example.com/mydoc.pdf`
- Monitor the worker logs to see the step by step execution of workflow.


## Design Decisions
### 1. Workflow & Activities Structure  
- **Temporal Python SDK**  
  - We define a single `@workflow.defn` class (`IngestWorkflow`) with one `@workflow.run` entrypoint.  
  - Every step (fetch, parse, embed, store) is its own `@activity.defn`.  This clear separation lets Temporal handle retries, timeouts, and state for each logical unit.

### 2. Using `asyncio` for Concurrency  
- **Non‐blocking I/O in Activities**  
  - Activities like `fetch_document` and `generate_embedding` perform network I/O (HTTP, Cohere API).  By using `aiohttp` and letting the Temporal Worker run on an `asyncio` event loop, we avoid blocking OS threads and can process many activity tasks concurrently in the same process.  
- **Batch Embedding (Option B)**  
  - We opted to run each embedding call in its own Activity but could also batch multiple chunks inside one Activity via `asyncio.gather()` if needed for higher throughput.

### 3. ChromaDB Schema  
- We use a single collection named `documents` with:  
  - **IDs**: `"<file_id>::<chunk_index>"`  
  - **Embeddings**: 1024‑dim float vectors (Cohere)  
  - **Metadatas**: storing `{ file_id, chunk_index }` for retrieval filtering  
  - **Documents**: the raw chunk text  
- This flat schema enables straightforward similarity search and metadata filtering.

### 4. Assumptions  
- **File Size & Chunking**: We assume documents can be reasonably partitioned into ~500‑word chunks; very large docs may need streaming or pagination enhancements.  
- **Local ChromaDB**: We run ChromaDB in‑process for ease of local development.  In production, you’d point to a dedicated Chroma server or managed vector store.  
- **Cohere Quotas**: We rely on Cohere’s free embedding tier but assume rate limits are modest; heavy workloads should implement client‑side rate throttling or batch requests.

---
By organizing around Temporal’s Workflow/Activity paradigm, layering in asyncio I/O concurrency, and carefully classifying errors, this pipeline is both resilient and  scalable.



