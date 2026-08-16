"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Info } from "lucide-react";
import Link from "next/link";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { KeywordDetailSkeleton } from "@/components/loading-skeletons";
import { PageHeading } from "@/components/page-heading";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type KeywordData = {
  id: string;
  keyword: string;
  language: string;
  geo: string;
  provider: string;
  current: number | null;
  average: number | null;
  growth: number | null;
  trend: number | null;
  volatility: number | null;
  z_score: number | null;
  robust_z_score: number | null;
  percentile: number | null;
  competition: number | null;
  bid: number | null;
  monthly_volumes: { year: number; month: number; searches: number }[];
  explanations: string[];
};

async function getKeyword(keywordId: string): Promise<KeywordData> {
  const response = await fetch(`${apiUrl}/api/keywords/${keywordId}`);
  if (!response.ok) throw new Error(response.status === 404 ? "Keyword not found." : "Keyword analytics are unavailable.");
  return response.json() as Promise<KeywordData>;
}

const integer = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function providerLabel(provider: string): string {
  if (provider === "mock") return "Demo data";
  if (provider === "csv") return "CSV import";
  if (provider === "google_ads") return "Google Ads";
  return "Search data";
}

export function KeywordDetail({ keywordId }: { keywordId: string }) {
  const query = useQuery({ queryKey: ["keyword", keywordId], queryFn: () => getKeyword(keywordId) });

  if (query.isLoading) return <KeywordDetailSkeleton />;
  if (query.isError || !query.data) return <div aria-live="polite" className="panel data-state error-state" role="alert">{query.error?.message ?? "Keyword not found."}</div>;

  const data = query.data;
  const chartData = data.monthly_volumes.map((item) => ({
    period: new Date(item.year, item.month - 1).toLocaleDateString("en-US", { month: "short" }),
    searches: item.searches,
  }));
  const metricGroups = [
    {
      title: "Demand level",
      description: "How much search demand exists now and in a typical month.",
      metrics: [
        ["Current", data.current === null ? "—" : integer.format(data.current)],
        ["Average", data.average === null ? "—" : integer.format(data.average)],
      ],
    },
    {
      title: "Momentum",
      description: "Whether demand is rising, and how steadily it is changing.",
      metrics: [
        ["Growth", data.growth === null ? "—" : `${(data.growth * 100).toFixed(1)}%`],
        ["Trend", data.trend === null ? "—" : data.trend.toFixed(3)],
        ["Volatility", data.volatility === null ? "—" : data.volatility.toFixed(3)],
      ],
    },
    {
      title: "Relative signal",
      description: "How unusual today’s demand is compared with its own history.",
      metrics: [
        ["Z score", data.z_score === null ? "—" : data.z_score.toFixed(2)],
        ["Robust Z", data.robust_z_score === null ? "—" : data.robust_z_score.toFixed(2)],
        ["Percentile", data.percentile === null ? "—" : `${data.percentile.toFixed(1)}%`],
      ],
    },
    {
      title: "Commercial pressure",
      description: "How strongly advertisers compete and what a click may cost.",
      metrics: [
        ["Competition", data.competition === null ? "—" : data.competition.toFixed(1)],
        ["Bid", data.bid === null ? "—" : `$${data.bid.toFixed(2)}`],
      ],
    },
  ];

  return (
    <>
      <Link className="back-link" href="/discover"><ArrowLeft size={14} /> Back to discovery</Link>
      <PageHeading eyebrow={`${providerLabel(data.provider)} · ${data.geo} · ${data.language}`} title={data.keyword} description="Twelve-month demand history and deterministic statistical interpretation." />
      <section className="keyword-detail-grid">
        <article className="panel keyword-chart-card">
          <div className="panel-heading"><div><p className="eyebrow">Demand history</p><h2>12-month search volume</h2></div></div>
          <div className="keyword-chart">
            <ResponsiveContainer debounce={100} width="100%" height="100%">
              <AreaChart accessibilityLayer={false} data={chartData} margin={{ left: 4, right: 12 }}>
                <defs><linearGradient id="volume-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--primary)" stopOpacity={0.32} /><stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02} /></linearGradient></defs>
                <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                <XAxis dataKey="period" tick={{ fontSize: 11, fill: "var(--chart-axis)" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "var(--chart-axis)" }} tickLine={false} axisLine={false} tickFormatter={(value: number) => integer.format(value)} width={68} />
                <Tooltip formatter={(value) => [integer.format(Number(value)), "Searches"]} isAnimationActive={false} />
                <Area activeDot={{ r: 4, strokeWidth: 0 }} dataKey="searches" fill="url(#volume-fill)" stroke="var(--primary)" strokeWidth={2.5} type="monotone" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="panel explanation-card">
          <div className="panel-heading"><div><p className="eyebrow">Interpretation</p><h2>What the statistics mean</h2></div><Info size={17} /></div>
          {data.explanations.map((explanation) => <p key={explanation}>{explanation}</p>)}
          <small>Rule-based explanation generated from stored analytics; no LLM is used.</small>
        </article>
      </section>
      <section aria-label="Keyword metrics" className="metric-group-grid">
        {metricGroups.map((group, groupIndex) => (
          <article className="panel metric-group" key={group.title}>
            <header className="metric-group-heading">
              <span aria-hidden="true">{String(groupIndex + 1).padStart(2, "0")}</span>
              <div><h2>{group.title}</h2><p>{group.description}</p></div>
            </header>
            <dl className="metric-group-values">
              {group.metrics.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
            </dl>
          </article>
        ))}
      </section>
    </>
  );
}
