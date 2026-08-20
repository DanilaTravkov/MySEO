# Architecture

```text
Next.js analytical UI
          |
          v
FastAPI application + analytics engine
          |
          v
      PostgreSQL
```

The backend receives search data only through a provider-neutral `SearchDataProvider` protocol. Provider responses are stored as raw observations. Statistical calculations produce separate, versioned analysis records. Run-scoped deterministic clustering uses word/character TF-IDF, cosine similarity, and agglomerative clustering. Later stages add opportunity scoring and an LLM analyst without changing this boundary.

The API uses an application factory so tests can construct isolated instances. Configuration comes from environment variables. Alembic is the only supported mechanism for persistent schema changes.

## Analytics flow

```text
Raw monthly observations
          ↓
Per-keyword statistics
          ↓
Dataset percentile normalization
          ↓
Versioned KeywordAnalysis
          ↓
Distribution diagnostics / Opportunity scoring
```

Analyses are associated with the discovery run that defines their comparison population. Growth, slope, volatility, outlier metrics, and normality diagnostics are deterministic. Semantic scores such as tool intent and buildability are never inferred by the statistical layer.

## Monitoring flow

```text
SearchMonitor
      ↓ due or manual
DiscoveryRun (immutable snapshot)
      ↓ existing provider → analytics → clustering pipeline
compare with previous completed run
      ↓
MonitorSignal (derived, run-pair scoped)
```

`SearchMonitor` owns provider-neutral configuration and cadence. `DiscoveryRun` remains the snapshot boundary and optionally references its monitor; raw observations are never rewritten during comparison. `MonitorSignal` is derived data linked to both the current and previous runs.

The scheduler is a short-lived CLI process. It claims due monitors in PostgreSQL, advances their `next_run_at`, and executes each monitor independently. User-facing concepts are monitors, scans, and signals; jobs are an infrastructure detail. Queue-backed workers can replace the single process later without changing the domain model.
