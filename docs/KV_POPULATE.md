# Populating Azure Key Vault (`fastorc-kv`)

This document describes how to populate the Key Vault with the required secrets for the Requests Hub app.

Prerequisites
---------------
- Azure CLI authenticated (`az login`)
- `az` has the permissions to set secrets on `fastorc-kv`
- Resource group: `fastorc-rg` (adjust environment variables if different)

Secrets to add
---------------
- COSMOS_CONN: Azure Cosmos DB connection string
- COSMOS_DB: Cosmos DB name (default `fastorc`)
- COSMOS_CONTAINER: Cosmos container name (default `audit_events`)
- DATABASE_URL: SQLAlchemy database URL for Postgres
- TEMPORAL_ADDRESS: Temporal frontend endpoint (e.g. `temporal-frontend:7233`)
- SLACK_WEBHOOK: Slack webhook URL used by the notify activity (optional)

Quick CLI
---------
Interactive:

```bash
./scripts/populate_kv.sh --interactive
```

Non-interactive example:

```bash
./scripts/populate_kv.sh --noninteractive \
  --cosmos_conn "AccountEndpoint=...;AccountKey=...;" \
  --db fastorc --container audit_events \
  --database_url "postgresql+asyncpg://user:pass@host/db" \
  --temporal_address "temporal-frontend:7233" \
  --slack_webhook "https://hooks.slack.com/services/XXX"
```

Verification
------------
After running, verify secrets are present:

```bash
az keyvault secret show --vault-name fastorc-kv --name COSMOS_CONN
az keyvault secret show --vault-name fastorc-kv --name DATABASE_URL
```

Next steps
----------
- Create a User Assigned Managed Identity (UAMI), assign it the `Key Vault Secrets User` role scoped to the vault, and attach it to your Container Apps so they can retrieve secrets using `DefaultAzureCredential`.
- See `README.md` for local dev fallback guidance (use `.env`).
