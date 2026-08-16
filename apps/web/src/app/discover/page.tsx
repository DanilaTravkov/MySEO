import { PageHeading } from "@/components/page-heading";

import { DiscoveryWorkspace } from "./discovery-workspace";

export default function DiscoverPage() {
  return (
    <>
      <PageHeading
        eyebrow="Demand discovery"
        title="Turn a few ideas into a market map."
        description="Start with the themes you care about, then explore the language, momentum, and intent behind real search behavior."
      />
      <DiscoveryWorkspace />
    </>
  );
}
