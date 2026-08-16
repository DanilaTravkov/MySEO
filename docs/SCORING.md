# Opportunity scoring

Opportunity scoring is deterministic, versioned, and calculated in the backend. Provider adapters never calculate scores.

## Feature normalization

Metrics with different units are not added directly. Values are percentile-ranked within the relevant discovery dataset and mapped to `0..100`, using average ranks for ties.

| Component | Raw signal | Direction |
| --- | --- | --- |
| Demand | `log1p(avg_monthly_searches)` | Higher is better |
| Growth | Last-three-month growth | Higher is better |
| Commercial value | `log1p(mean(low_bid, high_bid))` | Higher is better |
| Low competition | Competition index | Lower is better |
| Stability | Coefficient of variation | Lower is better |

Missing inputs remain `null`; they are not silently converted to zero. A single valid value receives the neutral percentile score `50`.

Tool intent and buildability are semantic components introduced in later stages. The scoring engine already accepts them, but it does not fabricate them from statistical data.

## Formula

```text
Opportunity Score =
    0.20 × demand
  + 0.15 × growth
  + 0.15 × commercial_value
  + 0.15 × low_competition
  + 0.15 × tool_intent
  + 0.15 × buildability
  + 0.05 × stability
```

Every component and the final result is constrained to `0..100`. Weights must be non-negative and sum to exactly `1.0`.

Weights are configured through backend environment variables:

```text
SCORE_WEIGHT_DEMAND=0.20
SCORE_WEIGHT_GROWTH=0.15
SCORE_WEIGHT_COMMERCIAL=0.15
SCORE_WEIGHT_LOW_COMPETITION=0.15
SCORE_WEIGHT_TOOL_INTENT=0.15
SCORE_WEIGHT_BUILDABILITY=0.15
SCORE_WEIGHT_STABILITY=0.05
```

## Recommendations

| Score | Recommendation |
| ---: | --- |
| 0–39.99 | `IGNORE` |
| 40–59.99 | `WATCH` |
| 60–74.99 | `INVESTIGATE` |
| 75–84.99 | `STRONG` |
| 85–100 | `BUILD` |

Lower bounds are configurable with `RECOMMENDATION_WATCH_MIN`, `RECOMMENDATION_INVESTIGATE_MIN`, `RECOMMENDATION_STRONG_MIN`, and `RECOMMENDATION_BUILD_MIN`. They must remain strictly ordered within `0..100`.

`GET /api/analytics/scoring-config` exposes active numeric configuration; it never exposes secrets.

## Statistical interpretation

Normal fits and Shapiro–Wilk results are diagnostics, not assumptions. Search-demand distributions are analyzed empirically with skewness, kurtosis, classical Z-score, robust Z-score, and historical percentile. A non-significant p-value is reported as “normality was not rejected,” never as proof that data is Gaussian.

