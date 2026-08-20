# Search Demand Intelligence

An opportunity engine that turns search-demand signals into ranked, explainable software product opportunities. The current MVP includes discovery, statistical analytics, distribution diagnostics, and the Stage 5 analytics dashboard.

Search Monitoring adds a time dimension to that workflow. A monitor stores one repeatable provider configuration, links its immutable discovery runs, and derives change signals by comparing each completed run with its predecessor.

## Quick start

Copy `.env.example` to `.env`, then start PostgreSQL and the API:

```bash
docker compose up --build
```

Open `http://localhost:8000/health` for the health check and `http://localhost:8000/docs` for the API documentation.

Run the web app in a second terminal:

```bash
npm install
npm run dev:web
```

Open `http://localhost:3000/dashboard`. PostgreSQL, the API, and the web app all start with `docker compose up --build`.

## Credential-free discovery

Run the deterministic Mock provider (the default creates 500 keywords with 12 months each):

```bash
curl -X POST http://localhost:8000/api/discovery/mock \
  -H "Content-Type: application/json" \
  -d '{"seeds":["json","pdf","typescript"],"language":"en","geo":"US","limit":500}'
```

Import a UTF-8 CSV using the format in `docs/examples/sample-keywords.csv`:

```bash
curl -X POST http://localhost:8000/api/discovery/csv \
  -F "file=@docs/examples/sample-keywords.csv" \
  -F "language=en" -F "geo=US" -F "currency=USD"
```

CSV validation reports the exact row and column for malformed numbers, invalid months, and duplicate periods. Both flows work without external API credentials.

Every new discovery run is analyzed automatically. Useful endpoints:

```text
POST /api/analytics/runs/{run_id}    Recalculate a run idempotently
GET  /api/distributions             Distribution Lab data
GET  /api/analytics/scoring-config  Active weights and thresholds
GET  /api/dashboard                 Live dashboard summary
GET  /api/discovery/results         Latest or selected run table
GET  /api/keywords/{keyword_id}     Keyword history and explanation
GET  /api/opportunities             Ranked cards when clusters exist
GET  /api/monitors                  Saved search monitors and latest state
POST /api/monitors                  Create a repeatable market monitor
POST /api/monitors/{id}/runs        Capture a new snapshot and detect changes
POST /api/clustering/runs/{run_id}  Recalculate deterministic clusters
GET  /api/clusters                  Run-scoped cluster analytics
```

Every discovery run is clustered automatically with word and character TF-IDF,
cosine similarity, and agglomerative clustering. Configure the cutoff with
`CLUSTERING_SIMILARITY_THRESHOLD`. Cluster volume is presented as an **aggregated
search-demand signal**, not as unique monthly users.

Open `http://localhost:3000/distributions` for the empirical histogram, normal-fit diagnostic, Q–Q plot, and robust distribution statistics. See `docs/SCORING.md` for normalization and scoring details.

Open `http://localhost:3000/monitoring` to create a monitor, capture a baseline, compare later runs, and inspect derived signals. The credential-free implementation supports the deterministic mock provider. CSV remains manual because an uploaded file cannot refresh itself; Google Ads remains unavailable until a real provider and credentials are configured.

Run due monitors once with:

```bash
cd apps/api
uv run python -m app.scheduler
```

In production, configure one scheduler (for example a Render Cron Job running every 15 minutes) with `python -m app.scheduler`. The scheduler only claims monitors whose `next_run_at` is due; monitor cadence remains source-aware and is not the cron polling interval.

## Checks

```bash
npm run lint
npm run typecheck
npm test
cd apps/api
uv sync --extra dev
uv run ruff check .
uv run mypy app
uv run pytest
docker compose config
```

See [Architecture](docs/ARCHITECTURE.md) and [Manual setup](docs/MANUAL_SETUP.md) for details.
