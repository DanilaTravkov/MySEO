"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Check, ChevronsRight, LoaderCircle, Play } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ClusterGridSkeleton, ResultsTableSkeleton } from "@/components/loading-skeletons";
import { AppSelect } from "@/components/app-select";
import { readExperienceLevel } from "@/lib/experience-level";

import {
  filterAndSortKeywordRows,
  type KeywordFilters,
  type KeywordResultRow,
  type NumericSortKey,
  type SortDirection,
} from "@/lib/keyword-results";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const pageSize = 15;
const clusterGuideStorageKey = "myseo:cluster-guide-dismissed:v1";

type DiscoveryResults = {
  run_id: string;
  provider: string;
  completed_at: string | null;
  rows: KeywordResultRow[];
};

type RunResponse = { run_id: string };

type Cluster = {
  id: string;
  name: string;
  description: string | null;
  total_volume: number;
  median_volume: number | null;
  weighted_growth: number | null;
  median_competition: number | null;
  median_bid: number | null;
  keyword_count: number;
  similarity_threshold: number;
  algorithm_version: string;
  keywords: { id: string; keyword: string; similarity: number | null }[];
};

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | { message?: string } };
    if (typeof body.detail === "string") return body.detail;
    return body.detail?.message ?? `Request failed (${response.status}).`;
  } catch {
    return `Request failed (${response.status}).`;
  }
}

async function getResults(runId?: string): Promise<DiscoveryResults | null> {
  const suffix = runId ? `?run_id=${runId}` : "";
  const response = await fetch(`${apiUrl}/api/discovery/results${suffix}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(await readError(response));
  return response.json() as Promise<DiscoveryResults>;
}

async function getClusters(runId: string): Promise<Cluster[]> {
  const response = await fetch(`${apiUrl}/api/clusters?run_id=${runId}`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json() as Promise<Cluster[]>;
}

const compactNumber = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

function providerLabel(provider: string): string {
  if (provider === "mock") return "Demo data";
  if (provider === "csv") return "CSV import";
  if (provider === "google_ads") return "Google Ads";
  return "Data source";
}

function display(value: number | null, kind: "number" | "percent" | "score" = "number") {
  if (value === null) return "—";
  if (kind === "percent") return `${(value * 100).toFixed(1)}%`;
  if (kind === "score") return value.toFixed(1);
  return compactNumber.format(value);
}

function numericFilter(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

export function DiscoveryWorkspace() {
  const queryClient = useQueryClient();
  const [seeds, setSeeds] = useState("json, pdf, resume");
  const [geo, setGeo] = useState("US");
  const [language, setLanguage] = useState("en");
  const [provider, setProvider] = useState("mock");
  const [file, setFile] = useState<File | null>(null);
  const [runId, setRunId] = useState<string>();
  const [sortKey, setSortKey] = useState<NumericSortKey>("volume");
  const [direction, setDirection] = useState<SortDirection>("desc");
  const [page, setPage] = useState(1);
  const [rawFilters, setRawFilters] = useState({ volume: "", growth: "", competition: "", opportunity: "" });
  const [clusterGuideState, setClusterGuideState] = useState<"hidden" | "visible" | "leaving">("hidden");

  useEffect(() => {
    if (readExperienceLevel() === "advanced") return;
    if (localStorage.getItem(clusterGuideStorageKey) === "true") return;
    const revealTimer = window.setTimeout(() => setClusterGuideState("visible"), 0);
    return () => window.clearTimeout(revealTimer);
  }, []);

  function dismissClusterGuide() {
    localStorage.setItem(clusterGuideStorageKey, "true");
    setClusterGuideState("leaving");
  }

  const results = useQuery({
    queryKey: ["discovery-results", runId ?? "latest"],
    queryFn: () => getResults(runId),
  });
  const clusters = useQuery({
    queryKey: ["clusters", results.data?.run_id],
    queryFn: () => getClusters(results.data!.run_id),
    enabled: Boolean(results.data?.run_id),
  });

  const run = useMutation({
    mutationFn: async (): Promise<RunResponse> => {
      let response: Response;
      if (provider === "csv") {
        if (!file) throw new Error("Choose a CSV file first.");
        const body = new FormData();
        body.append("file", file);
        body.append("language", language);
        body.append("geo", geo);
        body.append("currency", "USD");
        response = await fetch(`${apiUrl}/api/discovery/csv`, { method: "POST", body });
      } else if (provider === "mock") {
        const seedList = seeds.split(/[\n,]+/).map((seed) => seed.trim()).filter(Boolean);
        if (!seedList.length) throw new Error("Add at least one seed.");
        response = await fetch(`${apiUrl}/api/discovery/mock`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seeds: seedList, language, geo, limit: 500 }),
        });
      } else {
        throw new Error("Google Ads is not configured in this environment.");
      }
      if (!response.ok) throw new Error(await readError(response));
      return response.json() as Promise<RunResponse>;
    },
    onSuccess: async (data) => {
      setRunId(data.run_id);
      setPage(1);
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const filters: KeywordFilters = useMemo(() => ({
    minVolume: numericFilter(rawFilters.volume),
    minGrowth: rawFilters.growth === "" ? null : Number(rawFilters.growth) / 100,
    maxCompetition: numericFilter(rawFilters.competition),
    minOpportunity: numericFilter(rawFilters.opportunity),
  }), [rawFilters]);
  const rows = useMemo(
    () => filterAndSortKeywordRows(results.data?.rows ?? [], filters, sortKey, direction),
    [results.data?.rows, filters, sortKey, direction],
  );
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const hasNextPage = currentPage < totalPages;
  const pageRows = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  function sort(column: NumericSortKey) {
    setDirection(sortKey === column && direction === "desc" ? "asc" : "desc");
    setSortKey(column);
  }

  const columns: { key: NumericSortKey; label: string; kind?: "number" | "percent" | "score" }[] = [
    { key: "volume", label: "Volume" },
    { key: "growth", label: "Growth", kind: "percent" },
    { key: "competition", label: "Competition", kind: "score" },
    { key: "bid", label: "Bid", kind: "score" },
    { key: "z_score", label: "Z-score", kind: "score" },
    { key: "tool_intent", label: "Tool intent", kind: "score" },
    { key: "opportunity_score", label: "Opportunity", kind: "score" },
  ];
  const runError = run.error?.message;
  const seedError = runError && /seed/i.test(runError) ? runError : undefined;
  const fileError = runError && /(csv|file)/i.test(runError) ? runError : undefined;
  const formError = runError && !seedError && !fileError ? runError : undefined;

  return (
    <div className="discovery-workspace">
      <section className="panel discovery-form" data-tour="discovery-form">
        <div className="discovery-fields">
          <label>
            <span aria-live="polite" className={seedError ? "field-label-error" : undefined} id={seedError ? "seed-error" : undefined}>{seedError ?? "Seeds"}</span>
            <input aria-describedby={seedError ? "seed-error" : undefined} aria-invalid={Boolean(seedError)} aria-label="Seeds" className="seed-input" placeholder="json, pdf, resume" type="text" value={seeds} onChange={(event) => { setSeeds(event.target.value); if (run.isError) run.reset(); }} />
          </label>
          <label>Geo<AppSelect ariaLabel="Geo" onChange={setGeo} options={[{ value: "US", label: "United States" }]} value={geo} /></label>
          <label>Language<AppSelect ariaLabel="Language" onChange={setLanguage} options={[{ value: "en", label: "English" }]} value={language} /></label>
          <label>Provider<AppSelect ariaLabel="Provider" onChange={(value) => { setProvider(value); if (run.isError) run.reset(); }} options={[{ value: "mock", label: "Demo data" }, { value: "csv", label: "CSV import" }, { value: "google_ads", label: "Google Ads" }]} value={provider} /></label>
          {provider === "csv" && <label><span aria-live="polite" className={fileError ? "field-label-error" : undefined} id={fileError ? "file-error" : undefined}>{fileError ?? "CSV file"}</span><input accept=".csv,text/csv" aria-describedby={fileError ? "file-error" : undefined} aria-invalid={Boolean(fileError)} aria-label="CSV file" type="file" onChange={(event) => { setFile(event.target.files?.[0] ?? null); if (run.isError) run.reset(); }} /></label>}
        </div>
        <button className="primary-button" disabled={run.isPending || provider === "google_ads"} onClick={() => run.mutate()} type="button">
          {run.isPending ? <LoaderCircle className="spin" size={15} /> : <Play size={15} />} Run Discovery
        </button>
        {formError && <p className="inline-error">{formError}</p>}
        {provider === "google_ads" && <p className="form-note">Google Ads is listed but remains unavailable until credentials are configured.</p>}
      </section>

      <section className="panel results-panel" data-tour="discovery-results">
        <div className="panel-heading results-heading">
          <div><p className="eyebrow">Results</p><h2>{results.data ? `${rows.length} of ${results.data.rows.length} keywords` : "Discovery dataset"}</h2></div>
          {results.data && results.data.provider !== "mock" && <span className="tag">{providerLabel(results.data.provider)}</span>}
        </div>
        <div className="filter-grid">
          {[{ key: "volume", label: "Min volume" }, { key: "growth", label: "Min growth %" }, { key: "competition", label: "Max competition" }, { key: "opportunity", label: "Min opportunity" }].map(({ key, label }) => (
            <label key={key}>{label}<input inputMode="decimal" value={rawFilters[key as keyof typeof rawFilters]} onChange={(event) => { setRawFilters((current) => ({ ...current, [key]: event.target.value })); setPage(1); }} /></label>
          ))}
        </div>
        {results.isLoading ? <ResultsTableSkeleton /> : results.isError ? <div className="data-state error-state">{results.error.message}</div> : !results.data ? <div className="data-state">Run discovery to create the first dataset.</div> : (
          <>
            <div className="table-scroll"><table className="keyword-table"><thead><tr><th>Keyword</th>{columns.map((column) => <th key={column.key}><button onClick={() => sort(column.key)} type="button">{column.label}{sortKey === column.key && (direction === "desc" ? <ArrowDown size={12} /> : <ArrowUp size={12} />)}</button></th>)}</tr></thead><tbody>{pageRows.map((row) => <tr key={row.id}><td><Link href={`/keywords/${row.id}`}>{row.keyword}</Link></td>{columns.map((column) => <td key={column.key}>{display(row[column.key], column.kind)}</td>)}</tr>)}</tbody></table></div>
            <div className="pagination">
              <div aria-live="polite" className="pagination-summary"><span>Page {currentPage} of {totalPages}</span></div>
              <div className="pagination-actions"><button className="secondary-button" disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)} type="button">Previous</button><button className="secondary-button" disabled={!hasNextPage} onClick={() => setPage(currentPage + 1)} type="button">Next</button><button aria-label="Go to last page" className="secondary-button pagination-last" disabled={!hasNextPage} onClick={() => setPage(totalPages)} type="button">Last <ChevronsRight size={14} /></button></div>
            </div>
          </>
        )}
      </section>

      {results.data && (
        <section className="panel cluster-panel" data-tour="keyword-clusters">
          <div className="panel-heading">
            <div><p className="eyebrow">Intent structure</p><h2>Keyword clusters</h2></div>
          </div>
          {clusterGuideState !== "hidden" ? (
            <div className={`cluster-guide${clusterGuideState === "leaving" ? " is-leaving" : ""}`} onAnimationEnd={() => { if (clusterGuideState === "leaving") setClusterGuideState("hidden"); }}>
              <div className="cluster-guide-cards">
                <div className="cluster-guide-card"><span>01</span><p><strong>What this is</strong>Related searches grouped by the user problem they appear to describe.</p></div>
                <div className="cluster-guide-card"><span>02</span><p><strong>How to read it</strong>Compare group size, combined demand, growth, and competitive pressure.</p></div>
                <div className="cluster-guide-card"><span>03</span><p><strong>What to do next</strong>Open representative searches and validate whether the group maps to one buildable job.</p></div>
              </div>
              <div className="cluster-guide-footer">
                <p><strong>Ready to explore?</strong><span>This introduction is only shown once. You can hide it when the workflow is clear.</span></p>
                <button aria-label="Dismiss the keyword cluster explanation" className="cluster-guide-dismiss" onClick={dismissClusterGuide} type="button"><Check size={15} /> Got it</button>
              </div>
            </div>
          ) : null}
          <p className="cluster-disclaimer"><strong>Directional, not additive.</strong> Similar searches can overlap, so combined demand is useful for comparison but is not a count of unique monthly users.</p>
          {clusters.isLoading ? <ClusterGridSkeleton /> : clusters.isError ? <div className="data-state error-state">{clusters.error.message}</div> : (
            <div className="cluster-grid">
              {clusters.data?.map((cluster) => (
                <article className="cluster-card" key={cluster.id}>
                  <div className="cluster-card-heading"><div><span>{cluster.keyword_count} searches</span><h3>{cluster.name}</h3></div><div aria-label={`Combined demand ${compactNumber.format(cluster.total_volume)}`} className="cluster-demand"><strong>{compactNumber.format(cluster.total_volume)}</strong></div></div>
                  <dl><div><dt>Median volume</dt><dd>{display(cluster.median_volume)}</dd></div><div><dt>Weighted growth</dt><dd>{display(cluster.weighted_growth, "percent")}</dd></div><div><dt>Competition</dt><dd>{display(cluster.median_competition, "score")}</dd></div><div><dt>Median bid</dt><dd>{cluster.median_bid === null ? "—" : `$${cluster.median_bid.toFixed(2)}`}</dd></div></dl>
                  <p className="cluster-sample-label">Representative searches</p>
                  <div className="cluster-keywords">{cluster.keywords.slice(0, 5).map((keyword) => <Link href={`/keywords/${keyword.id}`} key={keyword.id}>{keyword.keyword}</Link>)}</div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
