# Architecture Overview

## Non Functional Requirements
- Availability 99.5% monthly
- P95 response time < 250ms
- Zero-downtime deploys
- Basic audit trail
- Disaster recovery RPO 1h

## Security
- JWT-based auth
- HTTPS everywhere
- Secrets in env with rotation

## Scalability
App scales horizontally with stateless API and managed DB. Caching for hot paths.

## API Overview
Public REST API with versioning under /v1.

## Architecture Decisions
### Language
Decision: Python + FastAPI. Consequences: quick dev, async IO. Status: accepted.
### DB
Decision: PostgreSQL managed. Consequences: durability, SQL. Status: accepted.
### CI/CD
Decision: GitHub Actions. Consequences: PR-based pipeline. Status: accepted.