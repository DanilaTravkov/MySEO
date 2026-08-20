"use client";

import {
  Activity, ArrowRight, CalendarClock, Check, Clock3, LoaderCircle, Pause, Play,
  Plus, Radar, RefreshCw, Sparkles, X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import { AppSelect } from "@/components/app-select";

type MonitorRun = {
  id: string;
  status: string;
  trigger: string;
  started_at: string | null;
  completed_at: string | null;
  keyword_count: number;
  signal_count: number;
};

type MonitorSignal = {
  id: string;
  signal_type: string;
  severity: "low" | "medium" | "high";
  title: string;
  summary: string;
  magnitude: number | null;
  created_at: string;
};

type SearchMonitor = {
  id: string;
  name: string;
  provider: string;
  seeds: string[];
  language: string;
  geo: string;
  frequency: "manual" | "monthly";
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
  run_count: number;
  latest_run: MonitorRun | null;
  recent_signals: MonitorSignal[];
};

const apiBase = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const frequencyOptions = [
  { value: "monthly", label: "Monthly" },
  { value: "manual", label: "Manual only" },
];
const providerOptions = [{ value: "mock", label: "Mock dataset · demo" }];
const marketOptions = [
  { value: "US", label: "United States" },
  { value: "GB", label: "United Kingdom" },
  { value: "DE", label: "Germany" },
  { value: "RS", label: "Serbia" },
];
const languageOptions = [
  { value: "en", label: "English" },
  { value: "de", label: "German" },
  { value: "sr", label: "Serbian" },
];

async function responseError(response: Response): Promise<string> {
  try {
    const payload = await response.json() as { detail?: string | Array<{ msg?: string }> };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) return payload.detail[0]?.msg ?? "The request could not be completed.";
  } catch {
    // A gateway response can be non-JSON.
  }
  return response.status >= 500 ? "Monitoring is temporarily unavailable." : "The request could not be completed.";
}

function formatDate(value: string | null, fallback = "Not yet"): string {
  if (!value) return fallback;
  return new Intl.DateTimeFormat("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(new Date(value));
}

function signalLabel(type: string): string {
  return type.replaceAll("_", " ");
}

export function MonitoringWorkspace() {
  const [monitors, setMonitors] = useState<SearchMonitor[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [runs, setRuns] = useState<MonitorRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [name, setName] = useState("AI meeting assistants");
  const [seeds, setSeeds] = useState("ai meeting notes\nmeeting transcription\nai meeting assistant");
  const [provider, setProvider] = useState("mock");
  const [frequency, setFrequency] = useState("monthly");
  const [geo, setGeo] = useState("US");
  const [language, setLanguage] = useState("en");

  const loadMonitors = useCallback(async () => {
    const response = await fetch(`${apiBase}/api/monitors`, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseError(response));
    const data = await response.json() as SearchMonitor[];
    setMonitors(data);
    setSelectedId((current) => current && data.some((item) => item.id === current)
      ? current
      : data[0]?.id ?? null);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadMonitors()
        .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Unable to load monitors."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadMonitors]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    void fetch(`${apiBase}/api/monitors/${selectedId}/runs`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error(await responseError(response));
        return response.json() as Promise<MonitorRun[]>;
      })
      .then((data) => { if (active) setRuns(data); })
      .catch((loadError) => {
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load run history.");
      });
    return () => { active = false; };
  }, [selectedId]);

  const selected = useMemo(
    () => monitors.find((monitor) => monitor.id === selectedId) ?? null,
    [monitors, selectedId],
  );

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/monitors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          provider,
          seeds: seeds.split(/[\n,]+/).map((seed) => seed.trim()).filter(Boolean),
          frequency,
          geo,
          language,
          enabled: true,
          limit: 500,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response));
      const created = await response.json() as SearchMonitor;
      await loadMonitors();
      setSelectedId(created.id);
      setShowCreate(false);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create monitor.");
    } finally {
      setSaving(false);
    }
  }

  async function runNow(monitor: SearchMonitor) {
    setRunningId(monitor.id);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/monitors/${monitor.id}/runs`, { method: "POST" });
      if (!response.ok) throw new Error(await responseError(response));
      await loadMonitors();
      const history = await fetch(`${apiBase}/api/monitors/${monitor.id}/runs`, { cache: "no-store" });
      if (history.ok) setRuns(await history.json() as MonitorRun[]);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unable to run monitor.");
    } finally {
      setRunningId(null);
    }
  }

  async function toggleMonitor(monitor: SearchMonitor) {
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/monitors/${monitor.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !monitor.enabled }),
      });
      if (!response.ok) throw new Error(await responseError(response));
      await loadMonitors();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Unable to update monitor.");
    }
  }

  if (loading) return <section aria-label="Loading monitoring workspace" className="monitor-loading panel"><LoaderCircle className="spin" size={22} /><span>Loading monitors</span></section>;

  return (
    <div className="monitoring-workspace">
      <section className="monitor-command panel" data-tour="monitoring">
        <div><span className="monitor-command-icon"><Radar size={19} /></span><div><strong>Search monitors</strong><p>Each monitor keeps one market definition and a comparable history of discovery runs.</p></div></div>
        <button className="primary-button" onClick={() => setShowCreate((current) => !current)} type="button">{showCreate ? <X size={15} /> : <Plus size={15} />}{showCreate ? "Close" : "New monitor"}</button>
      </section>

      {showCreate ? <form className="monitor-create panel" onSubmit={create}>
        <header><div><p className="eyebrow">New search monitor</p><h2>Define the market once.</h2></div><span>Automatic sources only</span></header>
        <div className="monitor-create-grid">
          <label><span>Name</span><input maxLength={255} onChange={(event) => setName(event.target.value)} required value={name} /></label>
          <label className="monitor-seeds-field"><span>Seed queries</span><textarea onChange={(event) => setSeeds(event.target.value)} required rows={4} value={seeds} /></label>
          <label><span>Source</span><AppSelect ariaLabel="Monitor source" onChange={setProvider} options={providerOptions} value={provider} /></label>
          <label><span>Frequency</span><AppSelect ariaLabel="Monitor frequency" onChange={setFrequency} options={frequencyOptions} value={frequency} /></label>
          <label><span>Market</span><AppSelect ariaLabel="Monitor market" onChange={setGeo} options={marketOptions} value={geo} /></label>
          <label><span>Language</span><AppSelect ariaLabel="Monitor language" onChange={setLanguage} options={languageOptions} value={language} /></label>
        </div>
        <footer><p>Google Ads appears here only after a real provider and credentials are configured.</p><button className="primary-button" disabled={saving} type="submit">{saving ? <LoaderCircle className="spin" size={15} /> : <ArrowRight size={15} />}{saving ? "Creating" : "Create monitor"}</button></footer>
      </form> : null}

      {error ? <p aria-live="polite" className="monitor-error">{error}</p> : null}

      {monitors.length === 0 ? <section className="monitor-empty panel"><span><Activity size={24} /></span><p className="eyebrow">No monitors yet</p><h2>Create a repeatable market baseline.</h2><p>Run the same provider configuration over time, then let MySEO surface meaningful changes between snapshots.</p><button className="primary-button" onClick={() => setShowCreate(true)} type="button"><Plus size={15} /> Create first monitor</button></section> : <div className="monitor-layout">
        <aside className="monitor-list" aria-label="Search monitors">
          {monitors.map((monitor) => <button aria-pressed={selectedId === monitor.id} className={selectedId === monitor.id ? "monitor-card active" : "monitor-card"} key={monitor.id} onClick={() => setSelectedId(monitor.id)} type="button">
            <span className="monitor-card-status"><i className={monitor.enabled ? "active" : "paused"} />{monitor.enabled ? "Active" : "Paused"}</span>
            <strong>{monitor.name}</strong>
            <small>{monitor.provider === "mock" ? "Demo source" : monitor.provider} · {monitor.geo} · {monitor.language.toUpperCase()}</small>
            <dl><div><dt>Last scan</dt><dd>{formatDate(monitor.last_run_at)}</dd></div><div><dt>Next scan</dt><dd>{monitor.frequency === "manual" ? "Manual" : formatDate(monitor.next_run_at)}</dd></div></dl>
            <span className="monitor-card-foot">{monitor.latest_run?.keyword_count ?? 0} keywords · {monitor.latest_run?.signal_count ?? 0} signals <ArrowRight size={13} /></span>
          </button>)}
        </aside>

        {selected ? <section className="monitor-detail panel">
          <header className="monitor-detail-header"><div><p className="eyebrow">Search monitor</p><h2>{selected.name}</h2><span>{selected.seeds.join(" · ")}</span></div><div><button className="secondary-button" onClick={() => toggleMonitor(selected)} type="button">{selected.enabled ? <Pause size={14} /> : <Play size={14} />}{selected.enabled ? "Pause" : "Resume"}</button><button className="primary-button" disabled={runningId === selected.id} onClick={() => runNow(selected)} type="button">{runningId === selected.id ? <LoaderCircle className="spin" size={15} /> : <RefreshCw size={15} />}{runningId === selected.id ? "Scanning" : "Run now"}</button></div></header>

          <div className="monitor-metrics">
            <div><span>Keywords</span><strong>{selected.latest_run?.keyword_count ?? "—"}</strong><small>latest snapshot</small></div>
            <div><span>Signals</span><strong>{selected.latest_run?.signal_count ?? "—"}</strong><small>since previous run</small></div>
            <div><span>Runs</span><strong>{selected.run_count}</strong><small>comparable snapshots</small></div>
            <div><span>Cadence</span><strong>{selected.frequency === "monthly" ? "30d" : "On demand"}</strong><small>{selected.enabled ? "monitor active" : "monitor paused"}</small></div>
          </div>

          <div className="monitor-detail-grid">
            <section className="monitor-signals"><header><div><Sparkles size={15} /><strong>Recent signals</strong></div><span>{selected.recent_signals.length} detected</span></header>{selected.run_count < 2 ? <div className="monitor-baseline"><Radar size={22} /><strong>One more run creates the first comparison.</strong><p>The initial run is stored as a baseline. Signals begin when a later snapshot can be compared with it.</p></div> : selected.recent_signals.length === 0 ? <div className="monitor-baseline stable"><Check size={22} /><strong>No material changes detected.</strong><p>The latest snapshot stayed within the current signal thresholds.</p></div> : <div className="monitor-signal-list">{selected.recent_signals.map((signal) => <article key={signal.id}><span className={`signal-severity ${signal.severity}`}>{signal.severity}</span><div><small>{signalLabel(signal.signal_type)}</small><strong>{signal.title}</strong><p>{signal.summary}</p></div></article>)}</div>}</section>

            <section className="monitor-schedule"><header><CalendarClock size={15} /><strong>Schedule</strong></header><dl><div><dt>Status</dt><dd>{selected.enabled ? "Active" : "Paused"}</dd></div><div><dt>Frequency</dt><dd>{selected.frequency === "monthly" ? "Monthly" : "Manual only"}</dd></div><div><dt>Last scan</dt><dd>{formatDate(selected.last_run_at)}</dd></div><div><dt>Next scan</dt><dd>{selected.frequency === "manual" ? "Not scheduled" : formatDate(selected.next_run_at)}</dd></div></dl><p>Monthly cadence matches the refresh rhythm of historical search metrics.</p></section>
          </div>

          <section className="monitor-history"><header><div><Clock3 size={15} /><strong>Run history</strong></div><span>{runs.length} runs</span></header>{runs.length === 0 ? <p>No scans have run yet.</p> : <div className="monitor-history-table"><table><thead><tr><th>Run</th><th>Trigger</th><th>Started</th><th>Keywords</th><th>Changes</th><th>Status</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id}><td><code>{run.id.slice(0, 8)}</code></td><td>{run.trigger}</td><td>{formatDate(run.started_at)}</td><td>{run.keyword_count}</td><td>{run.signal_count}</td><td><span className={`monitor-run-status ${run.status}`}>{run.status}</span></td></tr>)}</tbody></table></div>}</section>
        </section> : null}
      </div>}
    </div>
  );
}
