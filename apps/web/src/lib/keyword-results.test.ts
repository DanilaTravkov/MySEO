import { expect, it } from "vitest";

import { filterAndSortKeywordRows, type KeywordResultRow } from "./keyword-results";

const rows: KeywordResultRow[] = [
  { id: "a", keyword: "alpha", volume: 100, growth: 0.2, competition: 70, bid: 2, z_score: 1, tool_intent: null, opportunity_score: null },
  { id: "b", keyword: "beta", volume: 400, growth: -0.1, competition: 35, bid: 4, z_score: -1, tool_intent: 80, opportunity_score: 75 },
  { id: "c", keyword: "gamma", volume: 250, growth: 0.5, competition: 20, bid: 3, z_score: 2, tool_intent: 60, opportunity_score: 90 },
];

it("filters the four Stage 5 dimensions and sorts numeric values", () => {
  const result = filterAndSortKeywordRows(
    rows,
    { minVolume: 200, minGrowth: 0, maxCompetition: 30, minOpportunity: 80 },
    "growth",
    "desc",
  );
  expect(result.map((row) => row.keyword)).toEqual(["gamma"]);
});

it("places unavailable future-stage scores after real values", () => {
  const result = filterAndSortKeywordRows(
    rows,
    { minVolume: null, minGrowth: null, maxCompetition: null, minOpportunity: null },
    "opportunity_score",
    "desc",
  );
  expect(result.map((row) => row.keyword)).toEqual(["gamma", "beta", "alpha"]);
});
