function SkeletonLine({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`skeleton-line ${className}`} />;
}

function LoadingLabel({ children }: { children: string }) {
  return <span className="sr-only" role="status">{children}</span>;
}

export function DashboardSkeleton() {
  return (
    <div className="dashboard-workspace skeleton-layout">
      <LoadingLabel>Loading dashboard</LoadingLabel>
      <section aria-hidden="true" className="metric-grid metric-grid-six">
        {Array.from({ length: 6 }, (_, index) => <article className="metric-card skeleton-metric" key={index}><SkeletonLine className="short" /><SkeletonLine className="value" /><SkeletonLine className="tiny" /></article>)}
      </section>
      <section aria-hidden="true" className="panel provider-panel skeleton-provider-panel">
        <SkeletonLine className="eyebrow-width" />
        <div className="provider-grid">{Array.from({ length: 3 }, (_, index) => <div className="provider-row skeleton-provider-row" key={index}><SkeletonLine className="dot" /><div><SkeletonLine className="provider-title" /><SkeletonLine className="provider-copy" /></div><SkeletonLine className="pill" /></div>)}</div>
      </section>
    </div>
  );
}

export function ResultsTableSkeleton() {
  return (
    <div className="results-skeleton skeleton-layout">
      <LoadingLabel>Loading discovery results</LoadingLabel>
      <div aria-hidden="true" className="table-scroll skeleton-table">
        <div className="skeleton-table-row header">{Array.from({ length: 8 }, (_, index) => <SkeletonLine className={index === 0 ? "keyword" : "cell"} key={index} />)}</div>
        {Array.from({ length: 15 }, (_, row) => <div className="skeleton-table-row" key={row}>{Array.from({ length: 8 }, (_, column) => <SkeletonLine className={column === 0 ? `keyword width-${row % 3}` : "cell"} key={column} />)}</div>)}
      </div>
      <div aria-hidden="true" className="pagination skeleton-pagination"><SkeletonLine className="page" /><div><SkeletonLine className="button" /><SkeletonLine className="button" /><SkeletonLine className="button" /></div></div>
    </div>
  );
}

export function ClusterGridSkeleton() {
  return (
    <div className="cluster-grid skeleton-layout">
      <LoadingLabel>Loading keyword clusters</LoadingLabel>
      {Array.from({ length: 3 }, (_, index) => <article aria-hidden="true" className="cluster-card skeleton-cluster-card" key={index}><div className="skeleton-cluster-heading"><div><SkeletonLine className="tiny" /><SkeletonLine className="cluster-title" /></div><SkeletonLine className="cluster-value" /></div><div className="skeleton-cluster-metrics">{Array.from({ length: 4 }, (_, metric) => <div key={metric}><SkeletonLine className="metric-label" /><SkeletonLine className="metric-value" /></div>)}</div><SkeletonLine className="sample-label" /><div className="skeleton-chips">{Array.from({ length: 4 }, (_, chip) => <SkeletonLine className={`chip chip-${chip}`} key={chip} />)}</div></article>)}
    </div>
  );
}

export function OpportunitySkeleton() {
  return (
    <section className="opportunity-grid skeleton-layout">
      <LoadingLabel>Loading opportunities</LoadingLabel>
      {Array.from({ length: 3 }, (_, index) => <article aria-hidden="true" className="panel opportunity-card skeleton-opportunity-card" key={index}><div className="skeleton-opportunity-heading"><div><SkeletonLine className="pill" /><SkeletonLine className="opportunity-title-line" /><SkeletonLine className="opportunity-copy" /><SkeletonLine className="opportunity-copy short" /></div><SkeletonLine className="opportunity-score" /></div><div className="score-grid skeleton-score-grid">{Array.from({ length: 6 }, (_, score) => <div key={score}><SkeletonLine className="metric-label" /><SkeletonLine className="metric-value" /></div>)}</div><SkeletonLine className="action" /></article>)}
    </section>
  );
}

export function DistributionSkeleton() {
  return (
    <div className="distribution-workspace skeleton-layout">
      <LoadingLabel>Loading distribution diagnostics</LoadingLabel>
      <section aria-hidden="true" className="distribution-toolbar panel skeleton-distribution-toolbar"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="select" /></div><SkeletonLine className="dataset" /></section>
      <section aria-hidden="true" className="distribution-chart-grid">{Array.from({ length: 2 }, (_, index) => <article className="panel distribution-chart-card skeleton-chart-card" key={index}><div className="skeleton-panel-heading"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="chart-title" /></div><SkeletonLine className="pill" /></div><div className="skeleton-chart"><i /><i /><i /><i /><i /><span /></div>{index === 0 ? <div className="skeleton-chart-footer legend"><SkeletonLine /><SkeletonLine /></div> : <div className="skeleton-chart-footer caption"><SkeletonLine /></div>}</article>)}</section>
      <section aria-hidden="true" className="panel diagnostics-panel skeleton-diagnostics"><div className="skeleton-panel-heading"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="chart-title" /></div></div><div className="diagnostics-grid">{Array.from({ length: 8 }, (_, index) => <div key={index}><SkeletonLine className="metric-label" /><SkeletonLine className="metric-value" /></div>)}</div><SkeletonLine className="diagnostic" /></section>
    </div>
  );
}

export function KeywordDetailSkeleton() {
  return (
    <>
      <LoadingLabel>Loading keyword analytics</LoadingLabel>
      <SkeletonLine className="back skeleton-layout" />
      <header aria-hidden="true" className="page-heading page-heading-workspace skeleton-page-heading skeleton-layout"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="heading-title" /><SkeletonLine className="heading-copy" /></div></header>
      <section aria-hidden="true" className="keyword-detail-grid skeleton-layout"><article className="panel keyword-chart-card skeleton-chart-card"><div className="skeleton-panel-heading"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="chart-title" /></div></div><div className="skeleton-chart keyword"><i /><i /><i /><i /><i /><span /></div></article><article className="panel explanation-card skeleton-explanation"><SkeletonLine className="eyebrow-width" /><SkeletonLine className="explanation-title" />{Array.from({ length: 4 }, (_, index) => <div key={index}><SkeletonLine /><SkeletonLine className="short" /></div>)}</article></section>
      <section aria-hidden="true" className="metric-group-grid skeleton-layout">{Array.from({ length: 4 }, (_, index) => <article className="panel metric-group skeleton-metric-group" key={index}><header className="metric-group-heading"><SkeletonLine className="group-number" /><div><SkeletonLine className="group-title" /><SkeletonLine className="group-copy" /></div></header><div className="metric-group-values">{Array.from({ length: index === 1 || index === 2 ? 3 : 2 }, (_, metric) => <div key={metric}><SkeletonLine className="metric-label" /><SkeletonLine className="group-value" /></div>)}</div></article>)}</section>
    </>
  );
}

export function ProfileSkeleton() {
  return (
    <div className="profile-workspace skeleton-layout">
      <LoadingLabel>Loading profile</LoadingLabel>
      <aside aria-hidden="true" className="profile-summary panel skeleton-profile-summary"><SkeletonLine className="avatar" /><SkeletonLine className="profile-name" /><SkeletonLine className="profile-email" /><SkeletonLine className="pill" /><div className="profile-summary-lines"><SkeletonLine /><SkeletonLine /></div><SkeletonLine className="action" /></aside>
      <section aria-hidden="true" className="profile-form panel skeleton-profile-form"><div className="skeleton-panel-heading"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="chart-title" /></div></div><SkeletonLine className="profile-intro" /><div className="profile-fields">{Array.from({ length: 4 }, (_, index) => <label key={index}><SkeletonLine className="field-label" /><SkeletonLine className="field" /></label>)}</div><footer><SkeletonLine className="footer-copy" /><SkeletonLine className="save-button" /></footer></section>
      <section aria-hidden="true" className="profile-experience panel skeleton-profile-experience"><div className="skeleton-panel-heading"><div><SkeletonLine className="eyebrow-width" /><SkeletonLine className="chart-title" /></div></div><SkeletonLine className="profile-intro" /><div><SkeletonLine /><SkeletonLine /></div></section>
    </div>
  );
}
