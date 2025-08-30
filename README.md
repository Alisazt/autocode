# CrewAI AutoDev Prototype

This repository contains a **simplified prototype** of the CrewAI AutoDev platform based off the provided specification in `crewai_autodev_enhanced (4).md`.  The goal of this codebase is to break the monolithic specification into a modular project structure that can be run and extended more easily.  The prototype focuses on clarity and maintainability rather than completeness; many complex pieces (e.g. Kubernetes job execution, advanced observability and cost analytics) are stubbed out or simplified.

## Project structure

```
autodev/
├── backend/                 # Python backend services
│   ├── __init__.py
│   ├── main.py             # FastAPI application entrypoint
│   ├── api/
│   │   ├── __init__.py
│   │   └── hitl.py        # HITL review API endpoints
│   ├── models/
│   │   ├── __init__.py    # Pydantic models (ExecutionJob, JobAttempt, etc.)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── guardrails.py  # Guardrails engine using JSON Schema validation
│   │   ├── state_machine.py # Execution state machine for workflow transitions
│   │   ├── budget_manager.py # Cost management & budget tracking
│   │   └── execution_engine.py # Celery-based execution engine (simplified)
├── frontend/               # React/Next.js frontend components
│   ├── components/
│   │   ├── CrewMonitor.tsx
│   │   └── TemplateSelector.tsx
│   ├── pages/
│   │   └── index.tsx      # Simple page that ties components together
│   └── README.md          # How to run the frontend (requires Next.js)
├── alerting/
│   └── rules.yml          # Alerting rules example (Prometheus/Alertmanager)
├── infrastructure/
│   └── s3-lifecycle.yaml  # S3 lifecycle and versioning configuration example
├── k8s/
│   └── worker-deployment.yaml # Example secure Kubernetes deployment
├── migrations/
│   └── 001_execution_tables.sql # Database schema with constraints and indexes
└── docker-compose.yml      # Local development environment configuration
```

## Getting started

### Backend

The backend is built with **FastAPI** and **Pydantic**.  It exposes a small subset of the HITL (Human‑in‑the‑loop) API and stubs for an execution engine.  To run it locally:

```bash
cd autodev
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic celery redis aiohttp jsonschema
uvicorn backend.main:app --reload
```

The execution engine uses Celery for job orchestration.  For the sake of simplicity in this prototype, you can start a Redis instance locally and run Celery workers via:

```bash
  # start redis (for example using docker)
  docker run -p 6379:6379 redis:alpine

  # start celery worker in another terminal
  source venv/bin/activate
  celery -A backend.services.execution_engine worker --loglevel=info
```

### Frontend

The frontend is written in TypeScript using React/Next.js and provides two components from the specification: **TemplateSelector** and **CrewMonitor**.  To run the frontend you need a Next.js environment.  Create a new Next.js app (e.g. via `npx create-next-app`) and copy the contents of the `frontend/components` and `frontend/pages` folders into the appropriate places in your project.  See `frontend/README.md` for more details.

### Database & infrastructure

The `migrations/001_execution_tables.sql` file contains a sample Postgres schema with idempotency keys and unique indexes.  The `docker-compose.yml` file illustrates how you might set up the backend, worker, Redis and Postgres for local development.  The `k8s/worker-deployment.yaml` and `infrastructure/s3-lifecycle.yaml` files provide examples of how to deploy the worker securely in Kubernetes and configure S3 lifecycle rules.

### Limitations

This prototype does **not** implement all features from the original specification.  In particular:

- Kubernetes job execution is stubbed out in favour of Celery tasks for local development.
- Observability (OpenTelemetry) and advanced cost tracking are simplified.
- Secrets management, authentication, and budget enforcement are placeholders.
- The frontend does not include a complete build configuration.

Nevertheless, this structure should provide a solid foundation for iterating towards a full implementation while keeping the code modular and easy to reason about.
