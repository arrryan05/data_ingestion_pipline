from datetime import timedelta
from temporalio import workflow
from activities.activities import (
    fetch_document,
    parse_document,
    generate_embedding,
    store_chunk,
)

@workflow.defn
class IngestWorkflow:
    @workflow.run
    async def run(self, file_id: str, file_url: str) -> None:
        # 1. Fetch document bytes (timeout: 5 min)
        document_bytes = await workflow.execute_activity(
            fetch_document,
            args=(file_url,),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # 2. Parse into text chunks (timeout: 5 min), passing file_url for extension detection
        chunks = await workflow.execute_activity(
            parse_document,
            args=(document_bytes, file_url),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # 3. For each chunk: generate embedding then store (2 min each)
        for idx, text in chunks:
            embedding = await workflow.execute_activity(
                generate_embedding,
                args=(text,),
                start_to_close_timeout=timedelta(minutes=2),
            )
            await workflow.execute_activity(
                store_chunk,
                args=({"file_id": file_id, "chunk_index": idx, "text": text, "embedding": embedding},),
                start_to_close_timeout=timedelta(minutes=2),
            )

        # 4. Final log
        workflow.logger.info(
            f"IngestWorkflow completed for file_id={file_id}: {len(chunks)} chunks"
        )
        
        
        

