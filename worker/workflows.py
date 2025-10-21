from temporalio import workflow, activity
from datetime import timedelta
import asyncio
from audit import write_audit_event

@activity.defn
async def validate_request(data):
    # Placeholder: validate request data
    print(f"Validating request: {data}")
    return True

@activity.defn
async def notify(channel, message=None):
    # Allow either notify((channel, message)) or notify(channel, message)
    if message is None and isinstance(channel, (list, tuple)):
        channel, message = channel
    # Placeholder: send notification (e.g., Slack)
    print(f"Notify {channel}: {message}")
    return True

@activity.defn
async def escalate(request_id):
    # Placeholder: escalate request
    print(f"Escalating request {request_id}")
    return True


@activity.defn
async def audit_event(payload):
    # payload expected to be a dict with keys: request_id, event_type, payload, workflow_id, run_id
    try:
        request_id = payload.get('request_id')
        event_type = payload.get('event_type')
        p = payload.get('payload', {})
        workflow_id = payload.get('workflow_id')
        run_id = payload.get('run_id')
        res = await write_audit_event(request_id, event_type, p, workflow_id=workflow_id, run_id=run_id)
        print(f"Audit event result: {res}")
        return res
    except Exception as e:
        print("Audit activity error:", e)
        return {"ok": False, "reason": str(e)}

@activity.defn
async def check_status(request_id):
    # Placeholder: check if request is still open
    print(f"Checking status for {request_id}")
    return True  # Simulate still open

@workflow.defn
class RequestWorkflow:
    @workflow.run
    async def run(self, request_id, sla_minutes: int = 120):
        # Normalize inputs: `tctl` sometimes passes a JSON array as a single input
        if isinstance(request_id, (list, tuple)):
            try:
                _rid = request_id[0]
                _sla = request_id[1] if len(request_id) > 1 else sla_minutes
                request_id = _rid
                sla_minutes = int(_sla)
            except Exception:
                # fall back to the provided values
                pass

        await workflow.execute_activity(
            validate_request,
            request_id,
            start_to_close_timeout=timedelta(seconds=30),
        )
        # notify expects a single input (channel, message) tuple
        await workflow.execute_activity(
            notify,
            ("slack", "Created request"),
            start_to_close_timeout=timedelta(seconds=30),
        )
        # record audit: created
        try:
            await workflow.execute_activity(
                audit_event,
                {
                    "request_id": request_id,
                    "event_type": "created",
                    "payload": {"sla_minutes": sla_minutes},
                    "workflow_id": workflow.info().workflow_id,
                    "run_id": workflow.info().run_id,
                },
                start_to_close_timeout=timedelta(seconds=20),
            )
        except Exception as e:
            print("Audit activity failed (ignored):", e)
        # Avoid creating a zero-length timer (temporal requires a positive StartToFireTimeout)
        try:
            sla_val = int(sla_minutes)
        except Exception:
            sla_val = sla_minutes if isinstance(sla_minutes, int) else 0

        if sla_val > 0:
            # Use timedelta to produce a proper Duration for the StartTimer command
            await workflow.sleep(timedelta(seconds=sla_val * 60))
        else:
            # immediate path when SLA is 0: proceed to status check without a timer
            pass
        still_open = await workflow.execute_activity(
            check_status,
            request_id,
            start_to_close_timeout=timedelta(seconds=30),
        )
        if still_open:
            await workflow.execute_activity(
                escalate,
                request_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            # record audit: escalated
            try:
                await workflow.execute_activity(
                    audit_event,
                    {
                        "request_id": request_id,
                        "event_type": "escalated",
                        "payload": {},
                        "workflow_id": workflow.info().workflow_id,
                        "run_id": workflow.info().run_id,
                    },
                    start_to_close_timeout=timedelta(seconds=20),
                )
            except Exception as e:
                print("Audit activity failed (ignored):", e)
