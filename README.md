# Requests Hub

A full-stack, event-driven platform for orchestrating internal requests (bug, access, data export) with SLA timers, escalation, and Azure integration.

## Features
- FastAPI backend (async SQLAlchemy, Pydantic v2, PostgreSQL)
- Temporal Python SDK for workflow orchestration
- React + TypeScript (Vite) frontend
- Azure Blob Storage (attachments), Cosmos DB (events), Key Vault (secrets)
- Docker + docker-compose for local dev
- GitHub Actions CI/CD
- Observability: structured logs, request IDs, /healthz
- Tests: pytest, pre-commit (ruff, black, mypy)

## Repo Layout
```
api/      # FastAPI app
worker/   # Temporal worker
web/      # React app
infra/    # Azure infra as code (optional)
docs/     # setup, architecture, decisions
.github/workflows/ # CI/CD
```

## Quickstart
1. Clone repo and install Docker
2. `docker-compose up --build`
3. Access:
   - API: http://localhost:8000
   - Web: http://localhost:3000
   - Temporal: http://localhost:7233

## Docs
- See `docs/architecture.md` for architecture and design decisions.
- OpenAPI docs at `/docs` when API is running.

---

For Azure deployment, see `infra/` and GitHub Actions workflow.
