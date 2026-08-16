"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Sigma } from "lucide-react";
import { useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DistributionSkeleton } from "@/components/loading-skeletons";
import { AppSelect } from "@/components/app-select";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const QQ_POINT_BUDGET = 180;

const metricOptions = [
  ["avg_monthly_searches", "Average monthly searches"],
  ["log_avg_monthly_searches", "Log average monthly searches"],
  ["growth", "Growth"],
  ["cpc", "CPC / bid"],
  ["competition", "Competition"],
  ["opportunity_score", "Opportunity score"],
  ["tool_intent", "Tool intent"],
  ["buildability", "Buildability"],
] as const;

type Metric = (typeof metricOptions)[number][0];

interface DistributionData {
  run_id: string;
  metric: string;
  label: string;
  normal_fit_label: string;
  histogram: Array<{ start: number; end: number; count: number; normal_fit: number | null }>;
  qq_points: Array<{ theoretical: number; observed: number }>;
  diagnostics: {
    mean: number | null;
    median: number | null;
    std: number | null;
    mad: number | null;
    skewness: number | null;
    kurtosis: number | null;
    shapiro_wilk_p_value: number | null;
    sample_size: number;
    summary: string;
  };
  insufficient_sample: boolean;
}

async function fetchDistribution(metric: Metric): Promise<DistributionData> {
  const response = await fetch(`${API_URL}/api/distributions?metric=${metric}`);
  if (!response.ok) {
    throw new Error(response.status === 404 ? "Run discovery to create a dataset." : "Unable to load diagnostics.");
  }
  return response.json() as Promise<DistributionData>;
}

function formatMetric(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "—";
  if (Math.abs(value) >= 1000) return Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 2 }).format(value);
  return Intl.NumberFormat("en", { maximumFractionDigits: 3 }).format(value);
}

function downsampleQqPoints(points: DistributionData["qq_points"]): DistributionData["qq_points"] {
  if (points.length <= QQ_POINT_BUDGET) return points;
  return Array.from({ length: QQ_POINT_BUDGET }, (_, index) => {
    const sourceIndex = Math.round(index * (points.length - 1) / (QQ_POINT_BUDGET - 1));
    return points[sourceIndex];
  });
}

export function DistributionLab() {
  const [metric, setMetric] = useState<Metric>("avg_monthly_searches");
  const query = useQuery({
    queryKey: ["distribution", metric],
    queryFn: () => fetchDistribution(metric),
  });

  if (query.isPending) {
    return <DistributionSkeleton />;
  }
  if (query.isError) {
    return <section className="panel distribution-loading error"><AlertTriangle size={22} /><p>{query.error.message}</p></section>;
  }

  const data = query.data;
  const histogram = data.histogram.map((item) => ({
    range: `${formatMetric(item.start)}–${formatMetric(item.end)}`,
    midpoint: (item.start + item.end) / 2,
    count: item.count,
    normalFit: item.normal_fit,
  }));
  const qq = downsampleQqPoints(data.qq_points);
  const diagnostics = [
    ["Mean", data.diagnostics.mean],
    ["Median", data.diagnostics.median],
    ["Std", data.diagnostics.std],
    ["MAD", data.diagnostics.mad],
    ["Skewness", data.diagnostics.skewness],
    ["Kurtosis", data.diagnostics.kurtosis],
    ["Shapiro–Wilk p", data.diagnostics.shapiro_wilk_p_value],
    ["Sample size", data.diagnostics.sample_size],
  ] as const;
  const qqStart = qq[0];
  const qqEnd = qq.at(-1);

  return (
    <div className="distribution-workspace">
      <section className="distribution-toolbar panel" data-tour="distribution-metric">
        <div>
          <p className="eyebrow">Dataset metric</p>
          <AppSelect ariaLabel="Dataset metric" onChange={(value) => setMetric(value as Metric)} options={metricOptions.map(([value, label]) => ({ value, label }))} value={metric} />
        </div>
        <div className="run-reference"><span>Dataset</span><code>Latest discovery</code></div>
      </section>

      {data.diagnostics.sample_size === 0 ? (
        <section className="panel distribution-loading"><Sigma size={23} /><p>No observations are available for {data.label.toLowerCase()}.</p></section>
      ) : (
        <>
          <section className="distribution-chart-grid">
            <article className="panel distribution-chart-card" data-tour="histogram">
              <div className="panel-heading"><div><p className="eyebrow">Empirical shape</p><h2>Histogram</h2></div><span className="tag">n = {data.diagnostics.sample_size}</span></div>
              <div className="distribution-chart">
                <ResponsiveContainer debounce={120} width="100%" height="100%">
                  <ComposedChart data={histogram} margin={{ top: 10, right: 14, left: 8, bottom: 34 }}>
                    <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="midpoint" label={{ value: `${data.label} value`, position: "insideBottom", offset: -22, fill: "var(--muted)", fontSize: 11 }} tickFormatter={formatMetric} tick={{ fontSize: 12, fill: "var(--muted)" }} />
                    <YAxis label={{ value: "Keyword count", angle: -90, position: "insideLeft", fill: "var(--muted)", fontSize: 11 }} tick={{ fontSize: 12, fill: "var(--muted)" }} />
                    <Tooltip isAnimationActive={false} labelFormatter={(value) => `Bin center: ${formatMetric(Number(value))}`} />
                    <Bar animationDuration={420} animationEasing="ease-out" dataKey="count" name="Empirical count" fill="var(--primary)" isAnimationActive radius={[5, 5, 0, 0]} />
                    <Line animationBegin={100} animationDuration={520} animationEasing="ease-out" dataKey="normalFit" name={data.normal_fit_label} stroke="var(--coral)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-legend"><span><i className="empirical" /> Empirical</span><span><i className="normal" /> {data.normal_fit_label}</span></div>
            </article>

            <article className="panel distribution-chart-card" data-tour="qq-plot">
              <div className="panel-heading"><div><p className="eyebrow">Normal diagnostic</p><h2>Q–Q plot</h2></div>{data.qq_points.length > qq.length && <span className="tag">{qq.length} of {data.qq_points.length} points</span>}</div>
              <div className="distribution-chart chart-reveal" key={`qq-${metric}`}>
                <ResponsiveContainer debounce={120} width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 14, left: 8, bottom: 34 }}>
                    <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="theoretical" name="Theoretical quantile" label={{ value: "Expected normal position", position: "insideBottom", offset: -22, fill: "var(--muted)", fontSize: 11 }} tick={{ fontSize: 12, fill: "var(--muted)" }} />
                    <YAxis type="number" dataKey="observed" name="Observed value" label={{ value: "Observed metric value", angle: -90, position: "insideLeft", fill: "var(--muted)", fontSize: 11 }} tickFormatter={formatMetric} tick={{ fontSize: 12, fill: "var(--muted)" }} />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(value) => formatMetric(Number(value))} isAnimationActive={false} />
                    {qqStart && qqEnd && data.diagnostics.mean !== null && data.diagnostics.std !== null && (
                      <ReferenceLine segment={[
                        { x: qqStart.theoretical, y: data.diagnostics.mean + data.diagnostics.std * qqStart.theoretical },
                        { x: qqEnd.theoretical, y: data.diagnostics.mean + data.diagnostics.std * qqEnd.theoretical },
                      ]} stroke="var(--coral)" strokeWidth={1.5} />
                    )}
                    <Scatter data={qq} fill="var(--primary)" isAnimationActive={false} />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <p className="chart-caption">Points close to the reference line are more consistent with a normal fit.</p>
            </article>
          </section>

          <section className="panel diagnostics-panel" data-tour="diagnostics">
            <div className="panel-heading"><div><p className="eyebrow">Distribution diagnostics</p><h2>{data.label}</h2></div></div>
            <div className="diagnostics-grid">
              {diagnostics.map(([label, value]) => <div key={label}><span>{label}</span><strong>{formatMetric(value)}</strong></div>)}
            </div>
            <div className={data.insufficient_sample ? "diagnostic-note warning" : "diagnostic-note"}>
              {data.insufficient_sample ? <AlertTriangle size={16} /> : <Sigma size={16} />}
              <p>{data.diagnostics.summary}</p>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
