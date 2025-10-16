# Setup Guide: Requests Hub

## Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

## Local Development
1. Clone the repo
2. `docker-compose up --build`
3. Access:
   - API: http://localhost:8000
   - Web: http://localhost:3000
   - Temporal: http://localhost:7233

## Running Tests
- Backend: `cd api && pytest`
- Worker: `cd worker && pytest`
- Frontend: `cd web && npm test`

## Linting & Formatting
- Backend: `cd api && ruff . && black --check . && mypy .`
- Frontend: `cd web && npm run lint`

## Deployment
- See `infra/` for Azure deployment scripts (Bicep/Terraform, optional)
- CI/CD via GitHub Actions (`.github/workflows/ci.yml`)

---

For architecture and design, see `docs/architecture.md`.
