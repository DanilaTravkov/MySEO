"use client";

import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "@/components/empty-state";
import { OpportunitySkeleton } from "@/components/loading-skeletons";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Opportunity = {
  id: string;
  title: string;
  description: string | null;
  opportunity_score: number;
  demand: number;
  growth: number;
  commercial: number;
  competition: number;
  tool_intent: number;
  buildability: number;
  recommendation: string;
  analyze_available: boolean;
};

async function getOpportunities(): Promise<Opportunity[]> {
  const response = await fetch(`${apiUrl}/api/opportunities`);
  if (!response.ok) throw new Error("Opportunity data is unavailable.");
  return response.json() as Promise<Opportunity[]>;
}

export function OpportunityBoard() {
  const query = useQuery({ queryKey: ["opportunities"], queryFn: getOpportunities });
  if (query.isLoading) return <OpportunitySkeleton />;
  if (query.isError) return <div aria-live="polite" className="panel data-state error-state" role="alert">{query.error.message}</div>;
  if (!query.data?.length) return <EmptyState title="No opportunities yet" description="Run a discovery to see the strongest opportunities here." />;

  return <section className="opportunity-grid">{query.data.map((item) => <article className="panel opportunity-card" key={item.id}><div className="opportunity-title"><div><span className="tag">{item.recommendation}</span><h2>{item.title}</h2><p>{item.description}</p></div><strong>{item.opportunity_score.toFixed(1)}</strong></div><div className="score-grid">{[["Demand", item.demand], ["Growth", item.growth], ["Commercial", item.commercial], ["Competition", item.competition], ["Tool intent", item.tool_intent], ["Buildability", item.buildability]].map(([label, value]) => <div key={String(label)}><span>{label}</span><strong>{Number(value).toFixed(1)}</strong></div>)}</div><button className="primary-button full-width" disabled={!item.analyze_available} type="button">Analyze</button></article>)}</section>;
}
