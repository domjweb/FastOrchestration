#!/usr/bin/env bash
# Populate fastorc-kv with required secrets for local/testing or CI.
# Usage: ./scripts/populate_kv.sh --interactive
#        ./scripts/populate_kv.sh --noninteractive \
#            --cosmos_conn "<conn>" --db fastorc --container audit_events \
#            --database_url "postgresql+asyncpg://user:pass@host/db" --temporal_address "temporal-frontend:7233" --slack_webhook "<url>"

set -euo pipefail
VAULT_NAME=${VAULT_NAME:-fastorc-kv}
RG=${RG:-fastorc-rg}

usage(){
  cat <<EOF
Populate Key Vault $VAULT_NAME with the app secrets.

Options:
  --interactive        Prompt for each secret
  --noninteractive     Read flags for secrets
  --cosmos_conn        Cosmos DB connection string
  --db                 Cosmos DB name (default: fastorc)
  --container          Cosmos container (default: audit_events)
  --database_url       SQLALCHEMY DATABASE_URL
  --temporal_address   TEMPORAL_ADDRESS
  --slack_webhook      SLACK_WEBHOOK

EOF
}

if [[ ${1:-} == "--interactive" ]]; then
  read -rp "COSMOS_CONN: " COSMOS_CONN
  read -rp "COSMOS_DB (fastorc): " COSMOS_DB
  COSMOS_DB=${COSMOS_DB:-fastorc}
  read -rp "COSMOS_CONTAINER (audit_events): " COSMOS_CONTAINER
  COSMOS_CONTAINER=${COSMOS_CONTAINER:-audit_events}
  read -rp "DATABASE_URL: " DATABASE_URL
  read -rp "TEMPORAL_ADDRESS (temporal-frontend:7233): " TEMPORAL_ADDRESS
  TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS:-temporal-frontend:7233}
  read -rp "SLACK_WEBHOOK: " SLACK_WEBHOOK
else
  # parse args
  while [[ $# -gt 0 ]]; do
    case $1 in
      --noninteractive) NONINTERACTIVE=1; shift;;
      --cosmos_conn) COSMOS_CONN=$2; shift 2;;
      --db) COSMOS_DB=$2; shift 2;;
      --container) COSMOS_CONTAINER=$2; shift 2;;
      --database_url) DATABASE_URL=$2; shift 2;;
      --temporal_address) TEMPORAL_ADDRESS=$2; shift 2;;
      --slack_webhook) SLACK_WEBHOOK=$2; shift 2;;
      --help) usage; exit 0;;
      *) echo "Unknown arg: $1"; usage; exit 1;;
    esac
  done
fi

if [[ -z "${COSMOS_CONN:-}" ]]; then
  echo "COSMOS_CONN must be set" >&2
  exit 1
fi

# Write secrets
az keyvault secret set --vault-name $VAULT_NAME --name COSMOS_CONN --value "$COSMOS_CONN"
az keyvault secret set --vault-name $VAULT_NAME --name COSMOS_DB --value "${COSMOS_DB:-fastorc}"
az keyvault secret set --vault-name $VAULT_NAME --name COSMOS_CONTAINER --value "${COSMOS_CONTAINER:-audit_events}"
az keyvault secret set --vault-name $VAULT_NAME --name DATABASE_URL --value "${DATABASE_URL:-}"
az keyvault secret set --vault-name $VAULT_NAME --name TEMPORAL_ADDRESS --value "${TEMPORAL_ADDRESS:-temporal-frontend:7233}"
az keyvault secret set --vault-name $VAULT_NAME --name SLACK_WEBHOOK --value "${SLACK_WEBHOOK:-}"

echo "Secrets written to vault: $VAULT_NAME"
