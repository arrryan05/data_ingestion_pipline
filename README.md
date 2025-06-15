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
┌───────────────┐       ┌─────────────┐        ┌─────────────┐
│  trigger CLI  ├─►│ Temporal Frontend ├─► Risk─┤  Workflow   │
└───────────────┘       └─────────────┘        │ Activities  │
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
- run **docker-compose up --build -d**   
- open worker logs with **docker-compose logs -f worker**
- In another terminal run **docker-compose exec worker bash** to start a bash terminal inside the worker
- Run a input in following format **python src/run_ingest.py --file-id example123 --file-url https://example.com/mydoc.pdf**
- Monitor the worker logs to see the step by step execution of workflow.


