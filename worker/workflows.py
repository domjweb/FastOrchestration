from temporalio import workflow, activity
import asyncio

@activity.defn
async def validate_request(data):
    # Placeholder: validate request data
    print(f"Validating request: {data}")
    return True

@activity.defn
async def notify(channel, message):
    # Placeholder: send notification (e.g., Slack)
    print(f"Notify {channel}: {message}")
    return True

@activity.defn
async def escalate(request_id):
    # Placeholder: escalate request
    print(f"Escalating request {request_id}")
    return True

@activity.defn
async def check_status(request_id):
    # Placeholder: check if request is still open
    print(f"Checking status for {request_id}")
    return True  # Simulate still open

@workflow.defn
class RequestWorkflow:
    @workflow.run
    async def run(self, request_id, sla_minutes: int = 120):
        await workflow.execute_activity(validate_request, request_id, start_to_close_timeout=30)
        await workflow.execute_activity(notify, ("slack", "#requests", "Created"), start_to_close_timeout=30)
        await workflow.sleep(sla_minutes * 60)
        still_open = await workflow.execute_activity(check_status, request_id, start_to_close_timeout=30)
        if still_open:
            await workflow.execute_activity(escalate, request_id, start_to_close_timeout=30)
