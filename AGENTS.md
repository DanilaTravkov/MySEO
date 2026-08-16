# Search Demand Intelligence — contributor rules

## Architecture

This repository is a monorepo. `apps/web` is the Next.js analytical UI, `apps/api` is the FastAPI application and analytics engine, and `packages/shared` contains cross-application contracts that do not own domain behavior. PostgreSQL is the source of truth. Alembic owns schema migrations.

Provider-specific code belongs behind a `SearchDataProvider` protocol. Application services may depend on that protocol, never on Google Ads, CSV, or mock implementation details. Keep the analytics engine inside the backend; do not create a separate ML service for the MVP.

## Naming

- Python modules, functions, variables, and database columns: `snake_case`.
- Python types, Pydantic models, and SQLAlchemy models: `PascalCase`.
- React components and TypeScript types: `PascalCase`.
- TypeScript functions, variables, and JSON fields: `camelCase`.
- URL paths, directories, and CSS classes: lowercase kebab-case where applicable.
- Migrations use descriptive names and must be reviewed for downgrade safety.

## Data boundaries

Raw provider observations and calculated analytics are separate domain concepts and must never be mixed in the same storage model. Preserve provider payloads as immutable raw data; write derived metrics into versioned analysis records. Do not rewrite raw observations during recalculation.

## Secrets

Never commit credentials or real secrets. Use environment variables and keep `.env`, private keys, service-account JSON files, and Google Ads configuration out of Git. Never return secrets to the browser, persist them in application tables, or write them to logs.

## Required verification

After any change, run the relevant tests, lint, and type checks. At minimum:

```bash
npm run lint
npm run typecheck
npm test
cd apps/api && uv sync --extra dev
uv run ruff check .
uv run mypy app
uv run pytest
docker compose config
```

Keep external APIs optional in tests. The complete MVP test suite must pass with mock providers only.
