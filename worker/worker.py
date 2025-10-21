from temporalio.worker import Worker
from workflows import RequestWorkflow, validate_request, notify, escalate, check_status, audit_event
import asyncio

async def main():
    # Connect to Temporal server (address from env or default)
    import os
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "temporal-system")
    from temporalio.client import Client

    # defensive: strip whitespace and show repr for debugging invalid port issues
    temporal_address = temporal_address.strip()
    print("DEBUG: TEMPORAL_ADDRESS repr:", repr(temporal_address))

    # validate host:port format
    if ":" not in temporal_address:
        raise SystemExit(f"Invalid TEMPORAL_ADDRESS (missing ':') -> {repr(temporal_address)}")
    host, port = temporal_address.rsplit(":", 1)
    if not port.isdigit():
        raise SystemExit(f"Invalid TEMPORAL_ADDRESS port -> {repr(port)} in {repr(temporal_address)}")

    client = await Client.connect(temporal_address, namespace=temporal_namespace)
    # Start worker for the task queue
    worker = Worker(
        client,
        task_queue="requests-hub",
        workflows=[RequestWorkflow],
        activities=[validate_request, notify, escalate, check_status, audit_event],
    )
    print("Worker started for task queue: requests-hub")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
