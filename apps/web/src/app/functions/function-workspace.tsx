"use client";

import { Check, ChevronRight, Clock3, Code2, Cpu, Play, Terminal } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { AppSelect } from "@/components/app-select";
import { updateCurrentUser } from "@/lib/auth-client";
import { cacheExperienceLevel, experienceLevelEvent, readExperienceLevel, type ExperienceLevel } from "@/lib/experience-level";

type ScanMode = "topic" | "market";
type RunStatus = "ready" | "queued" | "running" | "completed";
type Execution = {
  id: string;
  scope: string;
  runtime: string;
  region: string;
  duration: string;
  status: "Succeeded";
  started: string;
};

const runtimes = [
  { value: "python", label: "Python 3.12" },
  { value: "node", label: "Node.js 22" },
] as const;

const regions = [
  { value: "eu-central-1", label: "Frankfurt · eu-central-1" },
  { value: "eu-west-1", label: "Ireland · eu-west-1" },
  { value: "us-east-1", label: "N. Virginia · us-east-1" },
] as const;

const pythonTemplate = `from myseo import SearchContext, SearchResult

def handler(context: SearchContext) -> SearchResult:
    results = context.search(limit=100)

    return SearchResult(
        checked=len(results),
        findings=context.compare_with_latest(results),
        evidence=context.extract_signals(results),
    )`;

const nodeTemplate = `import { SearchResult } from "@myseo/runtime";

export async function handler(context) {
  const results = await context.search({ limit: 100 });

  return new SearchResult({
    checked: results.length,
    findings: context.compareWithLatest(results),
    evidence: context.extractSignals(results),
  });
}`;

const initialExecutions: Execution[] = [
  { id: "run_84f1", scope: "AI meeting notes", runtime: "Python 3.12", region: "eu-central-1", duration: "2.4s", status: "Succeeded", started: "12 min ago" },
  { id: "run_7dc9", scope: "Market-wide pulse", runtime: "Node.js 22", region: "eu-west-1", duration: "3.1s", status: "Succeeded", started: "Yesterday" },
  { id: "run_63aa", scope: "Invoice automation", runtime: "Python 3.12", region: "eu-central-1", duration: "1.8s", status: "Succeeded", started: "Aug 14" },
];

const statusCopy: Record<RunStatus, string> = {
  ready: "Ready to execute",
  queued: "Allocating runtime",
  running: "Checking live results",
  completed: "Execution completed",
};

export function FunctionWorkspace() {
  const [mode, setMode] = useState<ScanMode>("topic");
  const [topic, setTopic] = useState("AI meeting notes");
  const [runtime, setRuntime] = useState("python");
  const [region, setRegion] = useState("eu-central-1");
  const [code, setCode] = useState(pythonTemplate);
  const [status, setStatus] = useState<RunStatus>("ready");
  const [error, setError] = useState("");
  const [executions, setExecutions] = useState(initialExecutions);
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>("guided");
  const [experienceHydrated, setExperienceHydrated] = useState(false);
  const [accessError, setAccessError] = useState("");
  const timersRef = useRef<number[]>([]);

  useEffect(() => () => timersRef.current.forEach((timer) => window.clearTimeout(timer)), []);
  useEffect(() => {
    const syncExperienceLevel = () => {
      setExperienceLevel(readExperienceLevel());
      setExperienceHydrated(true);
    };
    const syncTimer = window.setTimeout(syncExperienceLevel, 0);
    window.addEventListener(experienceLevelEvent, syncExperienceLevel);
    window.addEventListener("storage", syncExperienceLevel);
    return () => {
      window.clearTimeout(syncTimer);
      window.removeEventListener(experienceLevelEvent, syncExperienceLevel);
      window.removeEventListener("storage", syncExperienceLevel);
    };
  }, []);

  function changeRuntime(value: string) {
    setRuntime(value);
    setCode(value === "python" ? pythonTemplate : nodeTemplate);
  }

  function runFunction() {
    if (mode === "topic" && !topic.trim()) {
      setError("Enter a topic before running the function.");
      return;
    }

    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current = [];
    setError("");
    setStatus("queued");
    timersRef.current.push(window.setTimeout(() => setStatus("running"), 380));
    timersRef.current.push(window.setTimeout(() => {
      const runtimeLabel = runtimes.find((item) => item.value === runtime)?.label ?? runtime;
      const scope = mode === "topic" ? topic.trim() : "Market-wide pulse";
      const execution: Execution = {
        id: `run_${Math.random().toString(16).slice(2, 6)}`,
        scope,
        runtime: runtimeLabel,
        region,
        duration: "2.2s",
        status: "Succeeded",
        started: "Just now",
      };
      setStatus("completed");
      setExecutions((current) => [execution, ...current].slice(0, 5));
    }, 1850));
  }

  const isExecuting = status === "queued" || status === "running";

  async function activateAdvancedWorkspace() {
    setAccessError("");
    try {
      const user = await updateCurrentUser({ experienceLevel: "advanced" });
      cacheExperienceLevel(user.experienceLevel);
    } catch (activationError) {
      setAccessError(activationError instanceof Error ? activationError.message : "Sign in to change your workspace level.");
    }
  }

  if (!experienceHydrated) return <section aria-hidden="true" className="function-access-gate function-access-loading panel"><span /><span /><span /></section>;

  if (experienceLevel === "guided") return (
    <section className="function-access-gate panel">
      <span className="function-access-icon"><Code2 size={22} /></span>
      <p className="eyebrow">Advanced workspace</p>
      <h2>Build repeatable checks with code.</h2>
      <p>Cloud functions are intended for API-driven workflows where you control the runtime, verification logic, and execution region.</p>
      <div className="function-access-points"><span><Check size={14} /> Run custom verification logic</span><span><Check size={14} /> Inspect execution logs and evidence</span><span><Check size={14} /> Prepare workflows for API access</span></div>
      {accessError ? <p aria-live="polite" className="auth-error">{accessError}</p> : null}
      <button className="primary-button" onClick={activateAdvancedWorkspace} type="button">Use advanced workspace <ChevronRight size={15} /></button>
      <small>This changes the product experience only. You can return to Guided workspace from your profile.</small>
    </section>
  );

  return (
    <div className="function-workspace">
      <section className="function-config panel">
        <div className="function-config-intro">
          <span className="function-kicker"><Code2 size={15} /> Verification function</span>
          <h2>Current-search audit</h2>
          <p>Check one topic in depth or scan broadly for meaningful changes across the latest search landscape.</p>
        </div>

        <div className="function-scope" role="group" aria-label="Verification scope">
          <button aria-pressed={mode === "topic"} className={mode === "topic" ? "active" : ""} onClick={() => setMode("topic")} type="button"><strong>Selected topic</strong><span>Focused result and signal check</span></button>
          <button aria-pressed={mode === "market"} className={mode === "market" ? "active" : ""} onClick={() => setMode("market")} type="button"><strong>Market-wide</strong><span>Broad change and anomaly scan</span></button>
        </div>

        <div className="function-config-fields">
          <label className={error ? "has-error" : ""}><span>{error || "Topic"}</span><input disabled={mode === "market"} onChange={(event) => { setTopic(event.target.value); setError(""); }} placeholder="e.g. AI meeting notes" value={topic} /></label>
          <label><span>Runtime</span><AppSelect ariaLabel="Function runtime" onChange={changeRuntime} options={runtimes} value={runtime} /></label>
          <label><span>Region</span><AppSelect ariaLabel="Execution region" onChange={setRegion} options={regions} value={region} /></label>
        </div>
      </section>

      <section className="function-builder">
        <article className="function-code-panel panel">
          <header><div><span className="function-file"><Code2 size={14} /> handler.{runtime === "python" ? "py" : "js"}</span><small>128 MB · 30s timeout</small></div><span className="function-runtime-state"><i /> Runtime ready</span></header>
          <div className="function-editor-shell">
            <div aria-hidden="true" className="function-line-numbers">{code.split("\n").map((_, index) => <span key={index}>{index + 1}</span>)}</div>
            <textarea aria-label="Function source code" onChange={(event) => setCode(event.target.value)} spellCheck={false} value={code} />
          </div>
          <footer><span>Entry point <code>handler</code></span><button className="primary-button" disabled={isExecuting} onClick={runFunction} type="button"><Play size={15} /> {isExecuting ? statusCopy[status] : "Run function"}</button></footer>
        </article>

        <aside className="function-output-panel panel" aria-live="polite">
          <header><div><Terminal size={15} /><strong>Latest output</strong></div><span className={`execution-state ${status}`}><i /> {statusCopy[status]}</span></header>
          <div className="function-output-metrics">
            <div><span>Queries checked</span><strong>{status === "completed" ? "148" : "100"}</strong></div>
            <div><span>Live pages</span><strong>{status === "completed" ? "132" : "91"}</strong></div>
            <div><span>Signals changed</span><strong>{status === "completed" ? "19" : "12"}</strong></div>
            <div><span>Runtime</span><strong>{status === "completed" ? "2.2s" : "2.4s"}</strong></div>
          </div>
          <div className="function-log">
            <p><span>12:04:18</span> Runtime initialized in {region}</p>
            <p><span>12:04:19</span> Search context loaded for {mode === "topic" ? topic || "selected topic" : "market-wide pulse"}</p>
            <p><span>12:04:20</span> Current result pages normalized</p>
            <p className="success"><span>12:04:21</span> Evidence package created successfully</p>
          </div>
          <div className="function-finding"><span>Strongest change</span><strong>Comparison-led pages are gaining visibility.</strong><p>Seven newly ranked pages now lead with direct product comparisons and recent-use evidence.</p><button type="button">Open evidence <ChevronRight size={14} /></button></div>
        </aside>
      </section>

      <section className="function-history panel">
        <header><div><p className="eyebrow">Execution history</p><h2>Recent runs</h2></div><span><Clock3 size={14} /> Last 30 days</span></header>
        <div className="function-history-table"><table><thead><tr><th>Execution</th><th>Scope</th><th>Runtime</th><th>Region</th><th>Duration</th><th>Status</th><th>Started</th></tr></thead><tbody>{executions.map((execution) => <tr key={execution.id}><td><code>{execution.id}</code></td><td>{execution.scope}</td><td><span className="runtime-cell"><Cpu size={13} /> {execution.runtime}</span></td><td>{execution.region}</td><td>{execution.duration}</td><td><span className="run-success"><Check size={12} /> {execution.status}</span></td><td>{execution.started}</td></tr>)}</tbody></table></div>
      </section>
    </div>
  );
}
