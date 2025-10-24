from datetime import datetime
import os
import uuid
import asyncio
import json
import time
from typing import Optional
try:
    # prefer azure.identity when available to read Key Vault secrets via managed identity
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient as KVSecretClient
    HAVE_KEYVAULT = True
except Exception:
    DefaultAzureCredential = None
    KVSecretClient = None
    HAVE_KEYVAULT = False

try:
    from azure.cosmos import CosmosClient, exceptions, PartitionKey
    COSMOS_AVAILABLE = True
except Exception:
    CosmosClient = None
    exceptions = None
    PartitionKey = None
    COSMOS_AVAILABLE = False

# Config
COSMOS_CONN = os.getenv("COSMOS_CONN", "")
COSMOS_DB = os.getenv("COSMOS_DB", "fastorc")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "audit_events")
AUDIT_RETRIES = int(os.getenv("AUDIT_RETRIES", "3"))
AUDIT_BACKOFF_BASE = float(os.getenv("AUDIT_BACKOFF_BASE", "0.5"))
KEYVAULT_URL = os.getenv("KEYVAULT_URL", "")
KEYVAULT_COSMOS_SECRET = os.getenv("KEYVAULT_COSMOS_SECRET", "COSMOS_CONN")

_client = None
_container = None


def _log_structured(level: str, action: str, payload: dict):
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "action": action,
        **payload,
    }
    print(json.dumps(entry))


async def _run_blocking(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


def _init_client_blocking():
    global _client, _container
    if _client is not None:
        return
    # If Key Vault is configured but no env var, try to fetch from Key Vault synchronously
    global COSMOS_CONN
    if not COSMOS_CONN and KEYVAULT_URL and HAVE_KEYVAULT:
        try:
            cred = DefaultAzureCredential()
            kv = KVSecretClient(vault_url=KEYVAULT_URL, credential=cred)
            s = kv.get_secret(KEYVAULT_COSMOS_SECRET)
            COSMOS_CONN = s.value
            _log_structured('info', 'keyvault_fetch', {'secret': KEYVAULT_COSMOS_SECRET})
        except Exception as e:
            _log_structured('warn', 'keyvault_fetch_failed', {'error': str(e)})
    if not COSMOS_AVAILABLE or not COSMOS_CONN:
        return
    try:
        _client = CosmosClient.from_connection_string(COSMOS_CONN)
        db = _client.create_database_if_not_exists(id=COSMOS_DB)
        # Use PartitionKey helper if available (proper form for SDK)
        if PartitionKey is not None:
            _container = db.create_container_if_not_exists(id=COSMOS_CONTAINER, partition_key=PartitionKey(path='/requestId'))
        else:
            _container = db.create_container_if_not_exists(id=COSMOS_CONTAINER, partition_key={'path': '/requestId'})
    except Exception as e:
        _client = None
        _container = None
        _log_structured("warn", "cosmos_init_failed", {"error": str(e)})


async def _ensure_client():
    # Run blocking init in executor once
    if _client is not None and _container is not None:
        return
    if not COSMOS_AVAILABLE or not COSMOS_CONN:
        return
    await _run_blocking(_init_client_blocking)


async def write_audit_event(request_id: str, event_type: str, payload: dict, workflow_id: Optional[str] = None, run_id: Optional[str] = None):
    """Write an audit event document to Cosmos DB with retries and structured logging.

    Returns: {"ok": True, "id": <doc_id>} or {"ok": False, "reason": ...}
    """
    await _ensure_client()
    if _container is None:
        _log_structured("info", "audit_no_cosmos", {"requestId": request_id, "eventType": event_type})
        return {"ok": False, "reason": "no-cosmos"}

    ts = datetime.utcnow().isoformat() + "Z"
    # Deterministic id for idempotency: prefer run_id or workflow_id plus event_type
    if run_id:
        doc_id = f"{run_id}-{event_type}"
    elif workflow_id:
        doc_id = f"{workflow_id}-{event_type}"
    else:
        doc_id = f"{request_id}-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    doc = {
        "id": doc_id,
        "requestId": str(request_id),
        "workflowId": workflow_id,
        "runId": run_id,
        "eventType": event_type,
        "timestamp": ts,
        "payload": payload or {},
    }

    last_exc = None
    for attempt in range(1, AUDIT_RETRIES + 1):
        try:
            # upsert_item is blocking; run in executor to make operation idempotent
            await _run_blocking(_container.upsert_item, doc)
            _log_structured("info", "audit_upsert", {"ok": True, "id": doc_id, "requestId": request_id, "eventType": event_type, "attempt": attempt})
            return {"ok": True, "id": doc_id}
        except Exception as e:
            last_exc = e
            _log_structured("warn", "audit_write_failed", {"error": str(e), "attempt": attempt, "requestId": request_id, "eventType": event_type})
            # exponential backoff
            backoff = AUDIT_BACKOFF_BASE * (2 ** (attempt - 1))
            await asyncio.sleep(backoff)

    _log_structured("error", "audit_write_giveup", {"requestId": request_id, "eventType": event_type, "error": str(last_exc)})
    return {"ok": False, "reason": str(last_exc)}


async def get_audit_events(request_id: str):
    """Fetch all audit events for a given request_id from Cosmos DB."""
    await _ensure_client()
    if _container is None:
        _log_structured("info", "audit_no_cosmos_read", {"requestId": request_id})
        return []
    try:
        query = "SELECT * FROM c WHERE c.requestId = @requestId"
        items = list(_container.query_items(
            query=query,
            parameters=[{"name": "@requestId", "value": request_id}],
            enable_cross_partition_query=True
        ))
        _log_structured("info", "audit_read_success", {"requestId": request_id, "count": len(items)})
        return items
    except Exception as e:
        _log_structured("error", "audit_read_failed", {"requestId": request_id, "error": str(e)})
        return []
