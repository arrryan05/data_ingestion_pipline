import argparse
import asyncio
from temporalio.client import Client
from workflows.ingest_workflow import IngestWorkflow

async def main():
    parser = argparse.ArgumentParser(description="Trigger IngestWorkflow")
    parser.add_argument("--file-id",  required=True, help="Unique File ID")
    parser.add_argument("--file-url", required=True, help="URL of the document")
    args = parser.parse_args()

    client = await Client.connect("temporal:7233")

    handle = await client.start_workflow(
        IngestWorkflow.run,                 
        args=[args.file_id, args.file_url], 
        id=f"ingest-{args.file_id}",        
        task_queue="ingest-pipeline",       
    )

    print("🚀 Workflow started!")
    print("  Workflow ID:", handle.id)
    print("  Run ID     :", handle.result_run_id)

if __name__ == "__main__":
    asyncio.run(main())
