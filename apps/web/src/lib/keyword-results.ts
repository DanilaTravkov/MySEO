export type KeywordResultRow = {
  id: string;
  keyword: string;
  volume: number | null;
  growth: number | null;
  competition: number | null;
  bid: number | null;
  z_score: number | null;
  tool_intent: number | null;
  opportunity_score: number | null;
};

export type KeywordFilters = {
  minVolume: number | null;
  minGrowth: number | null;
  maxCompetition: number | null;
  minOpportunity: number | null;
};

export type NumericSortKey = Exclude<keyof KeywordResultRow, "id" | "keyword">;
export type SortDirection = "asc" | "desc";

export function filterAndSortKeywordRows(
  rows: KeywordResultRow[],
  filters: KeywordFilters,
  sortKey: NumericSortKey,
  direction: SortDirection,
): KeywordResultRow[] {
  const filtered = rows.filter((row) => {
    if (filters.minVolume !== null && (row.volume ?? -Infinity) < filters.minVolume) return false;
    if (filters.minGrowth !== null && (row.growth ?? -Infinity) < filters.minGrowth) return false;
    if (
      filters.maxCompetition !== null &&
      (row.competition ?? Infinity) > filters.maxCompetition
    ) return false;
    if (
      filters.minOpportunity !== null &&
      (row.opportunity_score ?? -Infinity) < filters.minOpportunity
    ) return false;
    return true;
  });

  return filtered.sort((left, right) => {
    const leftValue = left[sortKey];
    const rightValue = right[sortKey];
    if (leftValue === null) return 1;
    if (rightValue === null) return -1;
    return direction === "asc" ? leftValue - rightValue : rightValue - leftValue;
  });
}
