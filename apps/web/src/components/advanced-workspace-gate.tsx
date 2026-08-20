"use client";

import { Check, Code2 } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { updateCurrentUser } from "@/lib/auth-client";
import {
  cacheExperienceLevel,
  experienceLevelEvent,
  readExperienceLevel,
  type ExperienceLevel,
} from "@/lib/experience-level";

export function AdvancedWorkspaceGate({ children }: { children: ReactNode }) {
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel | null>(null);

  useEffect(() => {
    const syncExperienceLevel = () => setExperienceLevel(readExperienceLevel());
    const syncTimer = window.setTimeout(syncExperienceLevel, 0);
    window.addEventListener(experienceLevelEvent, syncExperienceLevel);
    window.addEventListener("storage", syncExperienceLevel);
    return () => {
      window.clearTimeout(syncTimer);
      window.removeEventListener(experienceLevelEvent, syncExperienceLevel);
      window.removeEventListener("storage", syncExperienceLevel);
    };
  }, []);

  function switchToAdvanced() {
    cacheExperienceLevel("advanced");
    void updateCurrentUser({ experienceLevel: "advanced" }).catch(() => undefined);
  }

  if (experienceLevel === null) {
    return <section aria-label="Loading workspace level" className="advanced-access-gate advanced-access-loading panel"><span /><span /><span /></section>;
  }

  if (experienceLevel === "guided") {
    return (
      <section className="advanced-access-gate panel">
        <span className="advanced-access-icon"><Code2 size={22} /></span>
        <p className="eyebrow">Advanced workspace</p>
        <h1>More analytical control, when you need it.</h1>
        <p>Distribution Lab and Monitoring are advanced research tools. Switch workspace level to inspect statistical shape and track the same market over time.</p>
        <div className="advanced-access-points">
          <span><Check size={13} /> Distribution diagnostics</span>
          <span><Check size={13} /> Scheduled market monitoring</span>
        </div>
        <button className="primary-button" onClick={switchToAdvanced} type="button">Use advanced workspace</button>
        <small>You can switch back at any time from your profile.</small>
      </section>
    );
  }

  return <>{children}</>;
}
