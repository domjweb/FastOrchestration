# Architecture: Requests Hub

## Overview
Requests Hub is an event-driven platform for orchestrating internal requests (bug, access, data export) with SLA timers, escalation, and Azure integration.

### Key Flows
- **Request submitted** → Validated → Enriched → Assigned → Notified
- **SLA timer** (e.g., 2h) set on creation; if unresolved, auto-escalate and notify
- **Status changes** write events to Cosmos DB (polyglot persistence)

### Tech Stack
- **Frontend:** React + TypeScript (Vite)
- **Backend:** FastAPI, async SQLAlchemy, Pydantic v2, PostgreSQL
- **Workflow:** Temporal Python SDK (workflows/activities)
- **Data:** PostgreSQL (primary), Cosmos DB (events), Azure Blob (attachments)
- **Cloud:** Azure Blob, Cosmos, Key Vault, Managed Identity, Container Apps
- **DevOps:** Docker, docker-compose, GitHub Actions, pre-commit

### MVP Endpoints
- `POST /api/requests`        # create request
- `GET  /api/requests`        # list requests
- `PATCH /api/requests/{id}`  # update status
- `GET  /api/requests/{id}/events` # event timeline

### Observability
- Structured logs, request IDs, `/healthz` endpoint

### Security
- Key Vault for secrets, Managed Identity for local/dev

---

See `README.md` for setup. See code for details on each component.
