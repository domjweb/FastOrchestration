#!/usr/bin/env bash
# demo.sh - run a quick Temporal demo (assumes docker compose is configured and running)
set -euo pipefail

# Start stack
docker compose up -d

# Wait for frontend health
echo "Waiting for temporal frontend to be healthy..."
# Wait until tctl can list namespace
until docker exec -i fastorc-temporal-frontend-1 tctl --ns temporal-system namespace list >/dev/null 2>&1; do
  sleep 1
done

echo "Starting demo workflow..."
docker exec -i fastorc-temporal-frontend-1 \
  tctl --ns temporal-system wf start --taskqueue requests-hub --workflow_type RequestWorkflow --workflow_id demo-run-2 --input '["req-demo-2", 0]'

echo "Tailing worker logs (CTRL-C to exit)"
docker compose logs -f worker
