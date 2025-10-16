# Decision Log: Requests Hub

## 2025-10-14: Initial Architecture
- Chose FastAPI + async SQLAlchemy for Python backend (async, type-safe, OpenAPI)
- Temporal Python SDK for workflow orchestration (SLA timers, retries, escalation)
- React + Vite for fast, modern frontend
- PostgreSQL for primary data, Cosmos DB for event log (polyglot persistence)
- Azure Blob for attachments, Key Vault for secrets, Managed Identity for dev
- Docker + docker-compose for local dev, GitHub Actions for CI/CD

## 2025-10-14: MVP Scope
- Endpoints: create/list/update requests, upload attachment, event timeline
- Observability: logs, request IDs, /healthz
- Tests: pytest, pre-commit (ruff, black, mypy)

---

Update this file as major decisions are made.
