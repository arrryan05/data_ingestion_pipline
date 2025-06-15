import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from chromadb import Client as ChromaClient
from chromadb.config import Settings

from workflows.ingest_workflow import IngestWorkflow
from activities.activities import (
    fetch_document,
    parse_document,
    generate_embedding,
    store_chunk,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

chroma_client = ChromaClient(Settings(
    persist_directory=".chromadb"
))
if "documents" not in chroma_client.list_collections():
    chroma_client.get_or_create_collection(name="documents")
logging.info("✅ ChromaDB collection 'documents' ready")

async def main():
    # 1) Connect to Temporal
    for i in range(10):
        try:
            client = await Client.connect("temporal:7233")
            break
        except Exception as e:
            logging.warning(f"[Retry {i+1}/10] Waiting for Temporal... ({e})")
            await asyncio.sleep(5)
    else:
        raise RuntimeError("Temporal service not reachable")

    logging.info("✅ Connected to Temporal; starting worker…")

    # 2) Start the Temporal worker
    worker = Worker(
        client,
        task_queue="ingest-pipeline",
        workflows=[IngestWorkflow],
        activities=[fetch_document, parse_document, generate_embedding, store_chunk],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
