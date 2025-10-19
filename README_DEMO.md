FastOrc demo

This README describes how to run a short demo of Temporal processing in this repo.

Prerequisites
- Docker and Docker Compose

Quick demo steps
1. Start the stack
   docker compose up -d

2. Ensure the worker is running (in a separate terminal keep logs open):
   docker compose ps
   docker compose logs -f worker

3. Start a demo workflow (in another terminal):
   # use namespace temporal-system where the current worker is registered
   docker exec -i fastorc-temporal-frontend-1 \
     tctl --ns temporal-system wf start --taskqueue requests-hub --workflow_type RequestWorkflow --workflow_id demo-run-2 --input '["req-demo-2", 0]'

4. Observe the worker logs; you should see activity prints like:
   Validating request: ['req-demo-2', 0]
   Notify slack: Created request
   Checking status for req-demo-2
   Escalating request req-demo-2

Demo artifacts
- demo_artifacts/history_demo_run2.txt  (workflow history for demo-run-2)
- demo_artifacts/worker_logs_demo.txt   (worker logs captured during the demo)

Notes
- This is a demo/dev setup. For production, secure secrets, use a managed pooler, and run multiple worker replicas.
