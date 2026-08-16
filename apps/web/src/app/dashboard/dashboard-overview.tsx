"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, CalendarClock, Database, Radar, TrendingUp, Zap } from "lucide-react";

import { DashboardSkeleton } from "@/components/loading-skeletons";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type DashboardData = {
  total_discovered_keywords: number;
  active_opportunities: number;
  strong_opportunities: number;
  median_search_volume: number | null;
  median_growth: number | null;
  last_discovery_run: {
    id: string;
    provider: string;
    status: string;
    completed_at: string | null;
  } | null;
  providers: { id: string; name: string; status: string }[];
};

async function getDashboard(): Promise<DashboardData> {
  const response = await fetch(`${apiUrl}/api/dashboard`);
  if (!response.ok) throw new Error("Dashboard data is unavailable.");
  return response.json() as Promise<DashboardData>;
}

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

const providerPresentation: Record<string, { name: string; description: string }> = {
  mock: { name: "Demo dataset", description: "Explore with representative demand data" },
  csv: { name: "CSV imports", description: "Analyze your own historical exports" },
  google_ads: { name: "Google Ads", description: "Connect live Keyword Planner research" },
};

export function DashboardOverview() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });

  if (query.isLoading) return <DashboardSkeleton />;
  if (query.isError || !query.data) {
    return <div aria-live="polite" className="panel data-state error-state" role="alert">Unable to reach the analytics API.</div>;
  }

  const data = query.data;
  const lastRun = data.last_discovery_run;
  const lastProvider = lastRun
    ? providerPresentation[lastRun.provider]?.name ?? "Connected source"
    : null;
  const metrics = [
    { label: "Discovered keywords", value: numberFormat.format(data.total_discovered_keywords), note: "All completed runs", icon: Database },
    { label: "Active opportunities", value: numberFormat.format(data.active_opportunities), note: "Excludes ignored", icon: Radar },
    { label: "Strong opportunities", value: numberFormat.format(data.strong_opportunities), note: "Strong or build", icon: Zap },
    { label: "Median search volume", value: data.median_search_volume === null ? "—" : numberFormat.format(data.median_search_volume), note: "Latest run", icon: Activity },
    { label: "Median growth", value: data.median_growth === null ? "—" : `${(data.median_growth * 100).toFixed(1)}%`, note: "Latest run · 3m", icon: TrendingUp },
    { label: "Last discovery run", value: lastRun?.completed_at ? new Date(lastRun.completed_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—", note: lastRun ? `${lastProvider} · Completed` : "No completed run", icon: CalendarClock },
  ];

  return (
    <div className="dashboard-workspace">
      <section className="metric-grid metric-grid-six" data-tour="dashboard-metrics">
        {metrics.map(({ label, value, note, icon: Icon }) => (
          <article className="metric-card" key={label}>
            <div className="metric-top"><span>{label}</span><Icon size={16} /></div>
            <strong>{value}</strong><small>{note}</small>
          </article>
        ))}
      </section>
      <section className="panel provider-panel" data-tour="data-sources">
        <div className="panel-heading">
          <p className="eyebrow">Data sources</p>
        </div>
        <div className="provider-grid">
          {data.providers.map((provider) => {
            const presentation = providerPresentation[provider.id] ?? { name: provider.name, description: "Search demand source" };
            return <div className="provider-row" key={provider.id}>
              <span className={`provider-indicator ${provider.status}`} />
              <div><strong>{presentation.name}</strong><small>{presentation.description}</small></div>
              <span className="state-pill neutral">{provider.status === "available" ? "Ready" : "Not connected"}</span>
            </div>;
          })}
        </div>
      </section>
    </div>
  );
}
