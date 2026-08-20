import { AdvancedWorkspaceGate } from "@/components/advanced-workspace-gate";
import { PageHeading } from "@/components/page-heading";

import { MonitoringWorkspace } from "./monitoring-workspace";

export default function MonitoringPage() {
  return (
    <AdvancedWorkspaceGate>
      <PageHeading
        eyebrow="Continuous intelligence"
        title="Track what changes, not just what is large."
        description="Save a market, refresh it on a schedule, and turn changes in demand, competition, and search intent into signals."
      />
      <MonitoringWorkspace />
    </AdvancedWorkspaceGate>
  );
}
