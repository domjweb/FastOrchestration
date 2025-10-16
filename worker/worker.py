from temporalio.worker import Worker
from workflows import RequestWorkflow, validate_request, notify, escalate, check_status
import asyncio

async def main():
    # Connect to Temporal server (address from env or default)
    import os
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    from temporalio.client import Client
    client = await Client.connect(temporal_address)
    # Start worker for the task queue
    worker = Worker(
        client,
        task_queue="requests-hub",
        workflows=[RequestWorkflow],
        activities=[validate_request, notify, escalate, check_status],
    )
    print("Worker started for task queue: requests-hub")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
